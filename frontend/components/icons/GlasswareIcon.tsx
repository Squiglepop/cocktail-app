import { SVGProps } from 'react';

interface GlasswareIconProps extends SVGProps<SVGSVGElement> {
  glassware: string;
  className?: string;
}

// SVG wrapper with consistent Lucide-style props
const SvgWrapper = ({ children, className, ...props }: SVGProps<SVGSVGElement> & { children: React.ReactNode }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    {...props}
  >
    {children}
  </svg>
);

// Individual glass icons - designed for recognition at small sizes

const CoupeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Wide, shallow rounded bowl on stem */}
    <path d="M4 8 Q4 4 12 4 Q20 4 20 8 Q20 11 12 11 Q4 11 4 8" />
    <line x1="12" y1="11" x2="12" y2="18" />
    <line x1="8" y1="20" x2="16" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const NickAndNoraIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Smaller, more rounded bowl than coupe */}
    <path d="M6 9 Q6 4 12 4 Q18 4 18 9 Q18 12 12 12 Q6 12 6 9" />
    <line x1="12" y1="12" x2="12" y2="18" />
    <line x1="8" y1="20" x2="16" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const MartiniIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Classic V-shape */}
    <path d="M4 4 L12 12 L20 4" />
    <line x1="4" y1="4" x2="20" y2="4" />
    <line x1="12" y1="12" x2="12" y2="18" />
    <line x1="8" y1="20" x2="16" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const FluteIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall, narrow, slightly tapered */}
    <path d="M9 3 L8 13 Q8 15 12 15 Q16 15 16 13 L15 3" />
    <line x1="9" y1="3" x2="15" y2="3" />
    <line x1="12" y1="15" x2="12" y2="19" />
    <line x1="9" y1="21" x2="15" y2="21" />
    <line x1="12" y1="19" x2="12" y2="21" />
  </SvgWrapper>
);

const SaucerIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Very wide, very shallow bowl - champagne saucer */}
    <path d="M3 8 Q3 6 12 6 Q21 6 21 8 Q21 10 12 10 Q3 10 3 8" />
    <line x1="12" y1="10" x2="12" y2="18" />
    <line x1="8" y1="20" x2="16" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const RocksIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Short, wide tumbler */}
    <path d="M5 6 L6 18 L18 18 L19 6 Z" />
    <line x1="5" y1="6" x2="19" y2="6" />
  </SvgWrapper>
);

const DoubleRocksIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Taller version of rocks */}
    <path d="M5 4 L6 20 L18 20 L19 4 Z" />
    <line x1="5" y1="4" x2="19" y2="4" />
  </SvgWrapper>
);

const JulepCupIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tapered cup, wider at top, metal cup look */}
    <path d="M6 4 L5 20 L19 20 L18 4 Z" />
    <line x1="6" y1="4" x2="18" y2="4" />
    {/* Subtle frost/texture lines */}
    <line x1="7" y1="8" x2="17" y2="8" strokeOpacity="0.5" />
  </SvgWrapper>
);

const HighballIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall, straight cylinder */}
    <path d="M7 3 L7 20 L17 20 L17 3 Z" />
    <line x1="7" y1="3" x2="17" y2="3" />
  </SvgWrapper>
);

const CollinsIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Taller, narrower than highball */}
    <path d="M8 2 L8 21 L16 21 L16 2 Z" />
    <line x1="8" y1="2" x2="16" y2="2" />
  </SvgWrapper>
);

const CopperMugIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Barrel-shaped mug with handle */}
    <path d="M5 5 Q4 12 5 19 L17 19 Q18 12 17 5 Z" />
    <line x1="5" y1="5" x2="17" y2="5" />
    {/* Handle */}
    <path d="M17 7 Q21 7 21 12 Q21 17 17 17" fill="none" />
  </SvgWrapper>
);

const PilsnerIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall, flared at top */}
    <path d="M8 3 L6 20 L18 20 L16 3 Z" />
    <line x1="8" y1="3" x2="16" y2="3" />
  </SvgWrapper>
);

const TikiMugIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Distinctive tiki totem shape */}
    <path d="M7 3 L6 20 L18 20 L17 3 Z" />
    <line x1="7" y1="3" x2="17" y2="3" />
    {/* Tiki face details - simplified */}
    <ellipse cx="9" cy="9" rx="1.5" ry="1" />
    <ellipse cx="15" cy="9" rx="1.5" ry="1" />
    <path d="M9 14 L15 14" />
    <line x1="9" y1="14" x2="9" y2="16" />
    <line x1="12" y1="14" x2="12" y2="16" />
    <line x1="15" y1="14" x2="15" y2="16" />
  </SvgWrapper>
);

const HurricaneIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Hourglass/curved vase shape */}
    <path d="M7 3 Q5 8 7 12 Q5 16 7 20 L17 20 Q19 16 17 12 Q19 8 17 3 Z" />
    <line x1="7" y1="3" x2="17" y2="3" />
  </SvgWrapper>
);

const GobletIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Large rounded bowl on short stem */}
    <path d="M5 5 Q5 14 12 14 Q19 14 19 5 Q19 3 12 3 Q5 3 5 5" />
    <line x1="12" y1="14" x2="12" y2="18" />
    <line x1="8" y1="20" x2="16" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const PocoGrandeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Like hurricane but with stem - curved tulip */}
    <path d="M8 4 Q6 7 8 10 Q6 13 8 15 L16 15 Q18 13 16 10 Q18 7 16 4 Z" />
    <line x1="8" y1="4" x2="16" y2="4" />
    <line x1="12" y1="15" x2="12" y2="18" />
    <line x1="8" y1="20" x2="16" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const MargaritaIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Wide, stepped bowl - double rim */}
    <path d="M3 5 L12 10 L21 5" />
    <line x1="3" y1="5" x2="21" y2="5" />
    <path d="M7 5 L7 3 L17 3 L17 5" />
    <line x1="12" y1="10" x2="12" y2="18" />
    <line x1="8" y1="20" x2="16" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const SnifterIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Wide bottom, narrow top, short stem */}
    <path d="M8 4 Q4 10 6 15 Q8 17 12 17 Q16 17 18 15 Q20 10 16 4" />
    <line x1="8" y1="4" x2="16" y2="4" />
    <line x1="12" y1="17" x2="12" y2="19" />
    <line x1="9" y1="21" x2="15" y2="21" />
    <line x1="12" y1="19" x2="12" y2="21" />
  </SvgWrapper>
);

const WineGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Classic wine glass - larger bowl */}
    <path d="M7 4 Q5 10 8 14 Q10 16 12 16 Q14 16 16 14 Q19 10 17 4" />
    <line x1="7" y1="4" x2="17" y2="4" />
    <line x1="12" y1="16" x2="12" y2="19" />
    <line x1="8" y1="21" x2="16" y2="21" />
    <line x1="12" y1="19" x2="12" y2="21" />
  </SvgWrapper>
);

const IrishCoffeeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Footed mug with handle */}
    <path d="M6 4 L7 15 Q7 17 12 17 Q17 17 17 15 L18 4 Z" />
    <line x1="6" y1="4" x2="18" y2="4" />
    {/* Handle */}
    <path d="M18 6 Q22 6 22 10 Q22 14 18 14" fill="none" />
    {/* Short foot */}
    <line x1="12" y1="17" x2="12" y2="19" />
    <line x1="9" y1="20" x2="15" y2="20" />
    <line x1="12" y1="19" x2="12" y2="20" />
  </SvgWrapper>
);

const FizzGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Small, narrow, tapered - like a small collins */}
    <path d="M9 4 L8 20 L16 20 L15 4 Z" />
    <line x1="9" y1="4" x2="15" y2="4" />
  </SvgWrapper>
);

const PunchCupIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Small bowl with handle */}
    <path d="M5 6 Q5 14 12 14 Q19 14 19 6 Q19 4 12 4 Q5 4 5 6" />
    {/* Handle */}
    <path d="M19 7 Q23 7 23 10 Q23 13 19 13" fill="none" />
  </SvgWrapper>
);

const GlencairnIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tulip-shaped whisky glass - wide at bottom, narrow at top */}
    <path d="M9 4 Q6 8 6 14 Q6 18 12 18 Q18 18 18 14 Q18 8 15 4" />
    <line x1="9" y1="4" x2="15" y2="4" />
    <line x1="9" y1="20" x2="15" y2="20" />
    <line x1="12" y1="18" x2="12" y2="20" />
  </SvgWrapper>
);

const ShotGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Very small, slightly tapered */}
    <path d="M8 8 L9 18 L15 18 L16 8 Z" />
    <line x1="8" y1="8" x2="16" y2="8" />
    {/* Thick bottom */}
    <line x1="9" y1="20" x2="15" y2="20" />
    <line x1="9" y1="18" x2="9" y2="20" />
    <line x1="15" y1="18" x2="15" y2="20" />
  </SvgWrapper>
);

// Fallback generic glass
const GenericGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    <path d="M7 4 L8 18 L16 18 L17 4 Z" />
    <line x1="7" y1="4" x2="17" y2="4" />
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
