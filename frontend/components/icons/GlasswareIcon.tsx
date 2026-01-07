import { SVGProps } from 'react';

interface GlasswareIconProps extends SVGProps<SVGSVGElement> {
  glassware: string;
  className?: string;
}

// SVG wrapper - thicker strokes for detail visibility
const SvgWrapper = ({ children, className, ...props }: SVGProps<SVGSVGElement> & { children: React.ReactNode }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    {...props}
  >
    {children}
  </svg>
);

// Detailed glass icons with character - ice, garnishes, liquid levels

const CoupeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Elegant coupe bowl */}
    <path d="M4 6 Q4 10 12 10 Q20 10 20 6" />
    <path d="M4 6 Q4 4 12 4 Q20 4 20 6" />
    {/* Liquid level */}
    <path d="M6 6 Q6 8 12 8 Q18 8 18 6" strokeOpacity="0.5" />
    {/* Stem and base */}
    <line x1="12" y1="10" x2="12" y2="18" />
    <ellipse cx="12" cy="20" rx="4" ry="1.5" />
  </SvgWrapper>
);

const NickAndNoraIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Bell-shaped bowl */}
    <path d="M6 5 Q6 11 12 11 Q18 11 18 5 Q18 3 12 3 Q6 3 6 5" />
    {/* Liquid level */}
    <path d="M7 5 Q7 9 12 9 Q17 9 17 5" strokeOpacity="0.5" />
    {/* Cherry garnish */}
    <circle cx="12" cy="6" r="1.5" fill="currentColor" />
    {/* Stem and base */}
    <line x1="12" y1="11" x2="12" y2="18" />
    <ellipse cx="12" cy="20" rx="4" ry="1.5" />
  </SvgWrapper>
);

const MartiniIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Classic V bowl */}
    <line x1="3" y1="3" x2="21" y2="3" />
    <line x1="3" y1="3" x2="12" y2="12" />
    <line x1="21" y1="3" x2="12" y2="12" />
    {/* Liquid level */}
    <line x1="6" y1="6" x2="18" y2="6" strokeOpacity="0.5" />
    {/* Olive on pick */}
    <line x1="9" y1="4" x2="15" y2="8" strokeWidth="1" />
    <ellipse cx="10" cy="5" rx="1.5" ry="1" fill="currentColor" />
    {/* Stem and base */}
    <line x1="12" y1="12" x2="12" y2="18" />
    <ellipse cx="12" cy="20" rx="4" ry="1.5" />
  </SvgWrapper>
);

const FluteIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall narrow flute */}
    <path d="M9 2 Q8 7 9 11 Q10 13 12 13 Q14 13 15 11 Q16 7 15 2" />
    <line x1="9" y1="2" x2="15" y2="2" />
    {/* Bubbles */}
    <circle cx="11" cy="6" r="0.5" fill="currentColor" />
    <circle cx="13" cy="8" r="0.5" fill="currentColor" />
    <circle cx="11" cy="10" r="0.5" fill="currentColor" />
    {/* Stem and base */}
    <line x1="12" y1="13" x2="12" y2="18" />
    <ellipse cx="12" cy="20" rx="3" ry="1.5" />
  </SvgWrapper>
);

const SaucerIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Wide shallow saucer */}
    <path d="M2 6 Q2 9 12 9 Q22 9 22 6" />
    <path d="M2 6 Q2 4 12 4 Q22 4 22 6" />
    {/* Liquid */}
    <path d="M4 6 Q4 7.5 12 7.5 Q20 7.5 20 6" strokeOpacity="0.5" />
    {/* Stem and base */}
    <line x1="12" y1="9" x2="12" y2="17" />
    <ellipse cx="12" cy="19" rx="4" ry="1.5" />
  </SvgWrapper>
);

const RocksIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Short tumbler */}
    <path d="M5 5 L6 19 Q6 21 12 21 Q18 21 18 19 L19 5 Z" />
    {/* Liquid level */}
    <path d="M6 8 L18 8" strokeOpacity="0.5" />
    {/* Ice cubes */}
    <rect x="7" y="10" width="3" height="3" rx="0.5" strokeWidth="1" />
    <rect x="11" y="12" width="3" height="3" rx="0.5" strokeWidth="1" />
    <rect x="14" y="9" width="3" height="3" rx="0.5" strokeWidth="1" />
  </SvgWrapper>
);

const DoubleRocksIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Taller tumbler */}
    <path d="M5 3 L6 19 Q6 21 12 21 Q18 21 18 19 L19 3 Z" />
    {/* Liquid level */}
    <path d="M6 7 L18 7" strokeOpacity="0.5" />
    {/* Large ice cube */}
    <rect x="8" y="9" width="8" height="7" rx="1" strokeWidth="1" />
  </SvgWrapper>
);

const JulepCupIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tapered metal cup */}
    <path d="M7 3 L5 19 Q5 21 12 21 Q19 21 19 19 L17 3 Z" />
    {/* Frost texture lines */}
    <line x1="7" y1="7" x2="17" y2="7" strokeOpacity="0.3" />
    <line x1="6" y1="11" x2="18" y2="11" strokeOpacity="0.3" />
    <line x1="6" y1="15" x2="18" y2="15" strokeOpacity="0.3" />
    {/* Mint sprig garnish */}
    <ellipse cx="10" cy="1" rx="2" ry="1" />
    <ellipse cx="14" cy="1" rx="2" ry="1" />
    <line x1="12" y1="1" x2="12" y2="4" strokeWidth="1" />
  </SvgWrapper>
);

const HighballIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall straight glass */}
    <path d="M6 2 L6 19 Q6 21 12 21 Q18 21 18 19 L18 2 Z" />
    {/* Liquid level */}
    <path d="M7 5 L17 5" strokeOpacity="0.5" />
    {/* Ice cubes */}
    <rect x="8" y="7" width="3" height="3" rx="0.5" strokeWidth="1" />
    <rect x="12" y="9" width="3" height="3" rx="0.5" strokeWidth="1" />
    {/* Straw */}
    <line x1="15" y1="1" x2="14" y2="14" strokeWidth="1.5" />
  </SvgWrapper>
);

const CollinsIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall narrow collins */}
    <path d="M7 1 L7 19 Q7 21 12 21 Q17 21 17 19 L17 1 Z" />
    {/* Liquid level */}
    <path d="M8 4 L16 4" strokeOpacity="0.5" />
    {/* Ice and citrus */}
    <rect x="9" y="6" width="2.5" height="2.5" rx="0.5" strokeWidth="1" />
    <rect x="12" y="8" width="2.5" height="2.5" rx="0.5" strokeWidth="1" />
    {/* Lemon wheel */}
    <circle cx="14" cy="3" r="2" strokeWidth="1" />
    <line x1="13" y1="3" x2="15" y2="3" strokeWidth="0.5" />
  </SvgWrapper>
);

const CopperMugIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Barrel-shaped mug body */}
    <path d="M4 4 Q3 11 4 18 Q5 20 11 20 Q17 20 18 18 Q19 11 18 4 Z" />
    {/* Handle */}
    <path d="M18 6 Q22 6 22 11 Q22 16 18 16" strokeWidth="2" />
    {/* Frost/condensation lines */}
    <line x1="6" y1="8" x2="16" y2="8" strokeOpacity="0.3" />
    <line x1="5" y1="12" x2="17" y2="12" strokeOpacity="0.3" />
    {/* Lime wedge garnish */}
    <path d="M8 2 Q11 1 11 4 Q8 4 8 2" fill="currentColor" />
  </SvgWrapper>
);

const PilsnerIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Flared pilsner */}
    <path d="M8 2 Q6 10 6 16 Q6 20 12 20 Q18 20 18 16 Q18 10 16 2 Z" />
    {/* Liquid/foam level */}
    <path d="M8 5 Q12 4 16 5" strokeOpacity="0.5" />
    {/* Bubbles */}
    <circle cx="10" cy="10" r="0.5" fill="currentColor" />
    <circle cx="13" cy="12" r="0.5" fill="currentColor" />
    <circle cx="11" cy="15" r="0.5" fill="currentColor" />
  </SvgWrapper>
);

const TikiMugIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tiki totem body */}
    <path d="M6 3 L5 20 Q5 21 12 21 Q19 21 19 20 L18 3 Z" />
    {/* Tiki face */}
    <ellipse cx="8" cy="9" rx="1.5" ry="1" />
    <ellipse cx="16" cy="9" rx="1.5" ry="1" />
    <path d="M8 14 L16 14" />
    <line x1="8" y1="14" x2="8" y2="17" />
    <line x1="12" y1="14" x2="12" y2="17" />
    <line x1="16" y1="14" x2="16" y2="17" />
    {/* Umbrella garnish */}
    <path d="M14 1 Q18 1 18 3 L14 3 Z" fill="currentColor" />
    <line x1="14" y1="1" x2="14" y2="6" strokeWidth="1" />
  </SvgWrapper>
);

const HurricaneIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Hourglass hurricane shape */}
    <path d="M7 2 Q4 6 6 10 Q4 14 6 18 Q7 20 12 20 Q17 20 18 18 Q20 14 18 10 Q20 6 17 2 Z" />
    {/* Liquid level */}
    <path d="M7 6 Q5 10 7 12 Q9 13 12 13 Q15 13 17 12 Q19 10 17 6" strokeOpacity="0.5" />
    {/* Cherry and orange garnish */}
    <circle cx="10" cy="4" r="1.5" fill="currentColor" />
    <path d="M13 2 Q16 2 15 5 L12 4 Z" strokeWidth="1" />
  </SvgWrapper>
);

const GobletIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Large rounded goblet */}
    <path d="M5 4 Q3 9 6 13 Q9 15 12 15 Q15 15 18 13 Q21 9 19 4 Z" />
    <line x1="5" y1="4" x2="19" y2="4" />
    {/* Liquid level */}
    <path d="M6 6 Q5 10 8 12 Q10 13 12 13 Q14 13 16 12 Q19 10 18 6" strokeOpacity="0.5" />
    {/* Stem and base */}
    <line x1="12" y1="15" x2="12" y2="18" />
    <ellipse cx="12" cy="20" rx="4" ry="1.5" />
  </SvgWrapper>
);

const PocoGrandeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Curved tulip poco grande */}
    <path d="M7 3 Q4 6 6 10 Q4 13 7 15 Q9 16 12 16 Q15 16 17 15 Q20 13 18 10 Q20 6 17 3 Z" />
    {/* Liquid */}
    <path d="M8 6 Q6 9 8 11 Q10 12 12 12 Q14 12 16 11 Q18 9 16 6" strokeOpacity="0.5" />
    {/* Pineapple wedge */}
    <path d="M14 1 L17 1 L16 4 L13 4 Z" strokeWidth="1" />
    {/* Stem and base */}
    <line x1="12" y1="16" x2="12" y2="18" />
    <ellipse cx="12" cy="20" rx="3" ry="1.5" />
  </SvgWrapper>
);

const MargaritaIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Wide margarita bowl */}
    <path d="M2 5 Q2 8 12 11 Q22 8 22 5" />
    <line x1="2" y1="5" x2="22" y2="5" />
    {/* Salt rim dots */}
    <circle cx="4" cy="5" r="0.5" fill="currentColor" />
    <circle cx="7" cy="4.5" r="0.5" fill="currentColor" />
    <circle cx="10" cy="4.5" r="0.5" fill="currentColor" />
    <circle cx="14" cy="4.5" r="0.5" fill="currentColor" />
    <circle cx="17" cy="4.5" r="0.5" fill="currentColor" />
    <circle cx="20" cy="5" r="0.5" fill="currentColor" />
    {/* Lime wedge */}
    <path d="M17 3 Q20 2 20 5" strokeWidth="1.5" />
    {/* Stem and base */}
    <line x1="12" y1="11" x2="12" y2="17" />
    <ellipse cx="12" cy="19" rx="4" ry="1.5" />
  </SvgWrapper>
);

const SnifterIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Wide belly snifter */}
    <path d="M8 4 Q3 8 4 13 Q5 17 12 17 Q19 17 20 13 Q21 8 16 4" />
    <line x1="8" y1="4" x2="16" y2="4" />
    {/* Liquid level - low pour */}
    <path d="M7 12 Q6 14 12 14 Q18 14 17 12" strokeOpacity="0.5" />
    {/* Stem and base */}
    <line x1="12" y1="17" x2="12" y2="19" />
    <ellipse cx="12" cy="21" rx="3" ry="1" />
  </SvgWrapper>
);

const WineGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Classic wine bowl */}
    <path d="M6 4 Q4 8 6 12 Q8 15 12 15 Q16 15 18 12 Q20 8 18 4" />
    <line x1="6" y1="4" x2="18" y2="4" />
    {/* Wine level */}
    <path d="M7 7 Q6 10 9 12 Q11 13 12 13 Q13 13 15 12 Q18 10 17 7" strokeOpacity="0.5" />
    {/* Stem and base */}
    <line x1="12" y1="15" x2="12" y2="19" />
    <ellipse cx="12" cy="21" rx="4" ry="1.5" />
  </SvgWrapper>
);

const IrishCoffeeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Footed mug body */}
    <path d="M5 3 Q4 7 5 12 Q6 15 12 15 Q18 15 19 12 Q20 7 19 3 Z" />
    {/* Handle */}
    <path d="M19 5 Q22 5 22 9 Q22 13 19 13" strokeWidth="2" />
    {/* Coffee level */}
    <path d="M6 8 L18 8" strokeOpacity="0.5" />
    {/* Cream top */}
    <path d="M6 6 Q12 4 18 6" strokeWidth="2" />
    {/* Short stem and base */}
    <line x1="12" y1="15" x2="12" y2="18" />
    <ellipse cx="12" cy="20" rx="3" ry="1" />
  </SvgWrapper>
);

const FizzGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Small narrow fizz */}
    <path d="M8 4 L7 18 Q7 20 12 20 Q17 20 17 18 L16 4 Z" />
    {/* Liquid level */}
    <line x1="8" y1="7" x2="16" y2="7" strokeOpacity="0.5" />
    {/* Fizz bubbles */}
    <circle cx="10" cy="10" r="0.5" fill="currentColor" />
    <circle cx="13" cy="12" r="0.5" fill="currentColor" />
    <circle cx="11" cy="14" r="0.5" fill="currentColor" />
    <circle cx="14" cy="16" r="0.5" fill="currentColor" />
  </SvgWrapper>
);

const PunchCupIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Teacup style */}
    <path d="M4 6 Q3 10 5 14 Q7 16 12 16 Q17 16 19 14 Q21 10 20 6" />
    <line x1="4" y1="6" x2="20" y2="6" />
    {/* Handle */}
    <path d="M20 8 Q23 8 23 11 Q23 14 20 14" strokeWidth="1.5" />
    {/* Liquid with fruit */}
    <path d="M5 9 L19 9" strokeOpacity="0.5" />
    <circle cx="10" cy="11" r="1" fill="currentColor" />
    <circle cx="14" cy="12" r="1" fill="currentColor" />
  </SvgWrapper>
);

const GlencairnIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tulip nosing glass */}
    <path d="M9 4 Q5 7 5 12 Q5 17 12 17 Q19 17 19 12 Q19 7 15 4" />
    <line x1="9" y1="4" x2="15" y2="4" />
    {/* Whisky level - small pour */}
    <path d="M8 13 Q8 15 12 15 Q16 15 16 13" strokeOpacity="0.5" />
    {/* Short base */}
    <line x1="12" y1="17" x2="12" y2="19" />
    <ellipse cx="12" cy="21" rx="3" ry="1" />
  </SvgWrapper>
);

const ShotGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Small shot glass */}
    <path d="M7 7 L8 18 Q8 20 12 20 Q16 20 16 18 L17 7 Z" />
    {/* Liquid - filled */}
    <path d="M8 10 L16 10" strokeOpacity="0.5" />
    <path d="M8 10 Q8 18 12 18 Q16 18 16 10" strokeOpacity="0.3" fill="currentColor" fillOpacity="0.1" />
  </SvgWrapper>
);

// Fallback generic glass
const GenericGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    <path d="M6 4 L7 18 Q7 20 12 20 Q17 20 17 18 L18 4 Z" />
    <line x1="6" y1="4" x2="18" y2="4" />
    <line x1="7" y1="8" x2="17" y2="8" strokeOpacity="0.5" />
  </SvgWrapper>
);

// Map of glassware enum values to icon components
const glasswareIcons: Record<string, (props: SVGProps<SVGSVGElement>) => JSX.Element> = {
  // Stemmed
  coupe: CoupeIcon,
  nick_and_nora: NickAndNoraIcon,
  martini: MartiniIcon,
  flute: FluteIcon,
  saucer: SaucerIcon,
  // Short
  rocks: RocksIcon,
  double_rocks: DoubleRocksIcon,
  julep_cup: JulepCupIcon,
  // Tall
  highball: HighballIcon,
  collins: CollinsIcon,
  copper_mug: CopperMugIcon,
  pilsner: PilsnerIcon,
  // Specialty
  tiki_mug: TikiMugIcon,
  hurricane: HurricaneIcon,
  goblet: GobletIcon,
  poco_grande: PocoGrandeIcon,
  margarita: MargaritaIcon,
  snifter: SnifterIcon,
  wine_glass: WineGlassIcon,
  irish_coffee: IrishCoffeeIcon,
  fizz_glass: FizzGlassIcon,
  punch_cup: PunchCupIcon,
  glencairn: GlencairnIcon,
  shot_glass: ShotGlassIcon,
};

export function GlasswareIcon({ glassware, className, ...props }: GlasswareIconProps) {
  const IconComponent = glasswareIcons[glassware] || GenericGlassIcon;
  return <IconComponent className={className} {...props} />;
}

// Export individual icons for direct use if needed
export {
  CoupeIcon,
  NickAndNoraIcon,
  MartiniIcon,
  FluteIcon,
  SaucerIcon,
  RocksIcon,
  DoubleRocksIcon,
  JulepCupIcon,
  HighballIcon,
  CollinsIcon,
  CopperMugIcon,
  PilsnerIcon,
  TikiMugIcon,
  HurricaneIcon,
  GobletIcon,
  PocoGrandeIcon,
  MargaritaIcon,
  SnifterIcon,
  WineGlassIcon,
  IrishCoffeeIcon,
  FizzGlassIcon,
  PunchCupIcon,
  GlencairnIcon,
  ShotGlassIcon,
  GenericGlassIcon,
};
