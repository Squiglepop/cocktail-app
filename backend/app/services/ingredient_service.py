"""
Admin ingredient CRUD service.
"""
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.recipe import Ingredient, RecipeIngredient
from ..schemas.ingredient import (
    IngredientAdminCreate,
    IngredientAdminUpdate,
    DuplicateMatch as DuplicateMatchSchema,
    DuplicateGroup as DuplicateGroupSchema,
)


def list_ingredients(
    db: Session,
    page: int,
    per_page: int,
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
) -> Tuple[List[Ingredient], int]:
    query = db.query(Ingredient)

    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(Ingredient.name.ilike(f"%{escaped}%", escape="\\"))
    if type_filter:
        query = query.filter(Ingredient.type == type_filter)

    total = query.count()
    items = (
        query.order_by(Ingredient.name)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def get_by_id(db: Session, ingredient_id: str) -> Optional[Ingredient]:
    return db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()


def create_ingredient(
    db: Session, data: IngredientAdminCreate
) -> Optional[Ingredient]:
    existing = db.query(Ingredient).filter(
        func.lower(Ingredient.name) == func.lower(data.name)
    ).first()
    if existing:
        return None

    ingredient = Ingredient(**data.model_dump())
    db.add(ingredient)
    try:
        db.commit()
        db.refresh(ingredient)
        return ingredient
    except IntegrityError:
        db.rollback()
        return None


def update_ingredient(
    db: Session, ingredient: Ingredient, data: IngredientAdminUpdate
) -> Optional[Ingredient]:
    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = db.query(Ingredient).filter(
            func.lower(Ingredient.name) == func.lower(update_data["name"]),
            Ingredient.id != ingredient.id,
        ).first()
        if existing:
            return None

    for key, value in update_data.items():
        setattr(ingredient, key, value)

    try:
        db.commit()
        db.refresh(ingredient)
        return ingredient
    except IntegrityError:
        db.rollback()
        return None


def get_recipe_usage_count(db: Session, ingredient_id: str) -> int:
    return (
        db.query(func.count(RecipeIngredient.id))
        .filter(RecipeIngredient.ingredient_id == ingredient_id)
        .scalar()
    )


def delete_ingredient(db: Session, ingredient: Ingredient) -> Tuple[bool, int]:
    recipe_count = get_recipe_usage_count(db, ingredient.id)
    if recipe_count > 0:
        return False, recipe_count

    db.delete(ingredient)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        recipe_count = get_recipe_usage_count(db, ingredient.id)
        return False, recipe_count if recipe_count > 0 else 1
    return True, 0


# --- Duplicate Detection ---

STRIP_PREFIXES = [
    "freshly squeezed ", "freshly pressed ", "fresh ",
]
STRIP_SUFFIXES = [
    " (freshly squeezed)", " (fresh)", " (chilled)",
]
PAREN_PATTERN = r'\s*\([^)]*\)\s*$'

REASON_PRIORITY = {
    "exact_match_case_insensitive": 0,
    "variation_pattern": 1,
    "fuzzy_match": 2,
}


def _normalize_for_variation(name: str) -> str:
    """Lowercase FIRST, then strip prefixes/suffixes/parentheticals."""
    name = name.lower().strip()
    for prefix in STRIP_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    for suffix in STRIP_SUFFIXES:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    name = re.sub(PAREN_PATTERN, '', name)
    return name.strip()


def _find_exact_case_matches(
    ingredients: List[Ingredient],
) -> List[Tuple[Ingredient, Ingredient, float, str]]:
    """Group by lower(name) on raw names, return pairs."""
    groups: Dict[str, List[Ingredient]] = defaultdict(list)
    for ing in ingredients:
        groups[ing.name.lower()].append(ing)

    pairs = []
    for members in groups.values():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                pairs.append((members[i], members[j], 1.0, "exact_match_case_insensitive"))
    return pairs


def _find_fuzzy_matches(
    ingredients: List[Ingredient],
    threshold: float = 0.8,
) -> List[Tuple[Ingredient, Ingredient, float, str]]:
    """Pairwise SequenceMatcher on lower(name), return pairs above threshold."""
    pairs = []
    for i in range(len(ingredients)):
        for j in range(i + 1, len(ingredients)):
            ratio = SequenceMatcher(
                None,
                ingredients[i].name.lower(),
                ingredients[j].name.lower(),
            ).ratio()
            if ratio > threshold:
                pairs.append((ingredients[i], ingredients[j], ratio, "fuzzy_match"))
    return pairs


def _find_variation_matches(
    ingredients: List[Ingredient],
) -> List[Tuple[Ingredient, Ingredient, float, str]]:
    """Normalize names, match on normalized forms."""
    normalized = [(ing, _normalize_for_variation(ing.name)) for ing in ingredients]
    groups: Dict[str, List[Ingredient]] = defaultdict(list)
    for ing, norm in normalized:
        groups[norm].append(ing)

    pairs = []
    for norm_name, members in groups.items():
        if len(members) < 2:
            continue
        # Only count as variation if at least one member differs from its normalized form
        has_variation = any(
            ing.name.lower().strip() != norm_name for ing in members
        )
        if not has_variation:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                # Only emit pair if at least one member was actually transformed
                a_transformed = members[i].name.lower().strip() != norm_name
                b_transformed = members[j].name.lower().strip() != norm_name
                if a_transformed or b_transformed:
                    pairs.append((members[i], members[j], 1.0, "variation_pattern"))
    return pairs


def _build_groups(
    usage_counts: Dict[str, int],
    exact_matches: List[Tuple[Ingredient, Ingredient, float, str]],
    fuzzy_matches: List[Tuple[Ingredient, Ingredient, float, str]],
    variation_matches: List[Tuple[Ingredient, Ingredient, float, str]],
) -> List[DuplicateGroupSchema]:
    """Merge matches, deduplicate pairs, Union-Find grouping, build schemas."""
    all_pairs = exact_matches + variation_matches + fuzzy_matches

    if not all_pairs:
        return []

    # Deduplicate: same (id_a, id_b) pair keeps highest-priority reason
    best_pair: Dict[Tuple[str, str], Tuple[Ingredient, Ingredient, float, str]] = {}
    for ing_a, ing_b, score, reason in all_pairs:
        key = (min(ing_a.id, ing_b.id), max(ing_a.id, ing_b.id))
        if key not in best_pair:
            best_pair[key] = (ing_a, ing_b, score, reason)
        else:
            existing_reason = best_pair[key][3]
            if REASON_PRIORITY[reason] < REASON_PRIORITY[existing_reason]:
                best_pair[key] = (ing_a, ing_b, score, reason)

    deduplicated = list(best_pair.values())

    # Collect all ingredient objects by id
    ing_by_id: Dict[str, Ingredient] = {}
    for ing_a, ing_b, _, _ in deduplicated:
        ing_by_id[ing_a.id] = ing_a
        ing_by_id[ing_b.id] = ing_b

    # Union-Find
    parent: Dict[str, str] = {iid: iid for iid in ing_by_id}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Store per-pair reason/score for building DuplicateMatch objects
    pair_info: Dict[Tuple[str, str], Tuple[float, str]] = {}
    for ing_a, ing_b, score, reason in deduplicated:
        union(ing_a.id, ing_b.id)
        key = (min(ing_a.id, ing_b.id), max(ing_a.id, ing_b.id))
        pair_info[key] = (score, reason)

    # Collect groups by root
    group_members: Dict[str, List[str]] = defaultdict(list)
    for iid in ing_by_id:
        group_members[find(iid)].append(iid)

    # Build schema groups
    result = []
    for members in group_members.values():
        if len(members) < 2:
            continue

        # Pick target = highest usage count
        members_sorted = sorted(
            members, key=lambda iid: usage_counts.get(iid, 0), reverse=True
        )
        target_id = members_sorted[0]
        target_ing = ing_by_id[target_id]

        # Determine group_reason = highest-priority reason among all pairs in group
        group_reasons = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                key = (min(members[i], members[j]), max(members[i], members[j]))
                if key in pair_info:
                    group_reasons.append(pair_info[key][1])
        group_reason = min(group_reasons, key=lambda r: REASON_PRIORITY[r]) if group_reasons else "fuzzy_match"

        # Find each duplicate's reason/score relative to target (or any pair they're in)
        duplicates = []
        for dup_id in members_sorted[1:]:
            dup_ing = ing_by_id[dup_id]
            # Try pair with target first, then any pair in the group
            key_with_target = (min(target_id, dup_id), max(target_id, dup_id))
            if key_with_target in pair_info:
                score, reason = pair_info[key_with_target]
            else:
                # Union-Find guarantees this ingredient has at least one pair
                score, reason = next(
                    pair_info[(min(dup_id, oid), max(dup_id, oid))]
                    for oid in members
                    if oid != dup_id
                    and (min(dup_id, oid), max(dup_id, oid)) in pair_info
                )

            duplicates.append(DuplicateMatchSchema(
                ingredient_id=dup_ing.id,
                name=dup_ing.name,
                type=dup_ing.type,
                similarity_score=score,
                detection_reason=reason,
                usage_count=usage_counts.get(dup_id, 0),
            ))

        target_match = DuplicateMatchSchema(
            ingredient_id=target_ing.id,
            name=target_ing.name,
            type=target_ing.type,
            similarity_score=1.0,
            detection_reason=group_reason,
            usage_count=usage_counts.get(target_id, 0),
        )

        result.append(DuplicateGroupSchema(
            target=target_match,
            duplicates=duplicates,
            group_reason=group_reason,
        ))

    return result


def merge_ingredients(
    db: Session, target_id: str, source_ids: List[str]
) -> Tuple[int, int]:
    """Merge source ingredients into target. Returns (recipes_affected, sources_removed).

    Raises:
        ValueError: If target is in source_ids (self-merge).
        LookupError: If target or any source ingredient is not found.
    """
    from sqlalchemy import and_

    # Validate target exists
    target = db.query(Ingredient).filter(Ingredient.id == target_id).first()
    if not target:
        raise LookupError("Target ingredient not found")

    # Validate target not in sources
    if target_id in source_ids:
        raise ValueError("Cannot merge ingredient into itself")

    # Validate all sources exist
    sources = db.query(Ingredient).filter(Ingredient.id.in_(source_ids)).all()
    found_ids = {s.id for s in sources}
    missing = set(source_ids) - found_ids
    if missing:
        raise LookupError(f"Source ingredient(s) not found: {', '.join(sorted(missing))}")

    # Track affected recipes
    affected_recipe_ids = set()

    for source in sources:
        source_ri_rows = db.query(RecipeIngredient).filter(
            RecipeIngredient.ingredient_id == source.id
        ).all()

        for ri in source_ri_rows:
            affected_recipe_ids.add(ri.recipe_id)
            # Check if target already in this recipe
            existing_target_ri = db.query(RecipeIngredient).filter(
                and_(
                    RecipeIngredient.recipe_id == ri.recipe_id,
                    RecipeIngredient.ingredient_id == target_id,
                )
            ).first()

            if existing_target_ri:
                db.delete(ri)
            else:
                ri.ingredient_id = target_id

    # Flush RI changes so SQLAlchemy doesn't try to nullify FKs on source delete
    db.flush()

    # Delete source ingredients
    for source in sources:
        db.delete(source)

    db.commit()

    return (len(affected_recipe_ids), len(sources))


def detect_duplicates(db: Session) -> List[DuplicateGroupSchema]:
    """Orchestrate all three detection strategies."""
    all_ingredients = db.query(Ingredient).all()

    if len(all_ingredients) < 2:
        return []

    # Pre-compute usage counts in bulk
    usage_counts = dict(
        db.query(
            RecipeIngredient.ingredient_id,
            func.count(RecipeIngredient.id),
        ).group_by(RecipeIngredient.ingredient_id).all()
    )

    exact_matches = _find_exact_case_matches(all_ingredients)
    fuzzy_matches = _find_fuzzy_matches(all_ingredients, threshold=0.8)
    variation_matches = _find_variation_matches(all_ingredients)

    return _build_groups(usage_counts, exact_matches, fuzzy_matches, variation_matches)
