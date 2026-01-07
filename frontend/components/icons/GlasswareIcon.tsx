import { SVGProps } from 'react';

interface GlasswareIconProps extends SVGProps<SVGSVGElement> {
  glassware: string;
  className?: string;
}

// SVG wrapper with refined stroke styling
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

// Refined glass icons with elegant curves matching reference aesthetic

const CoupeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Wide, shallow elegant bowl */}
    <path d="M4 6 Q4 10 12 10 Q20 10 20 6" />
    <path d="M4 6 Q4 4 12 4 Q20 4 20 6" />
    <line x1="12" y1="10" x2="12" y2="18" />
    <path d="M8 20 Q12 19 16 20" />
  </SvgWrapper>
);

const NickAndNoraIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Smaller rounded bell-shaped bowl */}
    <path d="M6 5 Q6 11 12 11 Q18 11 18 5 Q18 3 12 3 Q6 3 6 5" />
    <line x1="12" y1="11" x2="12" y2="18" />
    <path d="M8 20 Q12 19 16 20" />
  </SvgWrapper>
);

const MartiniIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Classic elegant V-shape */}
    <line x1="4" y1="4" x2="20" y2="4" />
    <line x1="4" y1="4" x2="12" y2="12" />
    <line x1="20" y1="4" x2="12" y2="12" />
    <line x1="12" y1="12" x2="12" y2="18" />
    <path d="M8 20 Q12 19 16 20" />
  </SvgWrapper>
);

const FluteIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall elegant champagne flute */}
    <path d="M9 3 Q8 8 10 12 Q11 14 12 14 Q13 14 14 12 Q16 8 15 3" />
    <line x1="9" y1="3" x2="15" y2="3" />
    <line x1="12" y1="14" x2="12" y2="19" />
    <path d="M9 21 Q12 20 15 21" />
  </SvgWrapper>
);

const SaucerIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Very wide champagne saucer */}
    <path d="M2 7 Q2 9 12 9 Q22 9 22 7" />
    <path d="M2 7 Q2 5 12 5 Q22 5 22 7" />
    <line x1="12" y1="9" x2="12" y2="18" />
    <path d="M8 20 Q12 19 16 20" />
  </SvgWrapper>
);

const RocksIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Short wide tumbler with subtle taper */}
    <path d="M5 7 L6 19 Q6 20 12 20 Q18 20 18 19 L19 7" />
    <line x1="5" y1="7" x2="19" y2="7" />
  </SvgWrapper>
);

const DoubleRocksIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Taller tumbler */}
    <path d="M6 4 L7 19 Q7 20 12 20 Q17 20 17 19 L18 4" />
    <line x1="6" y1="4" x2="18" y2="4" />
  </SvgWrapper>
);

const JulepCupIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tapered metal julep cup */}
    <path d="M7 4 L5 19 Q5 20 12 20 Q19 20 19 19 L17 4" />
    <line x1="7" y1="4" x2="17" y2="4" />
  </SvgWrapper>
);

const HighballIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tall straight highball */}
    <path d="M7 3 L7 19 Q7 20 12 20 Q17 20 17 19 L17 3" />
    <line x1="7" y1="3" x2="17" y2="3" />
  </SvgWrapper>
);

const CollinsIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Taller narrower collins */}
    <path d="M8 2 L8 19 Q8 21 12 21 Q16 21 16 19 L16 2" />
    <line x1="8" y1="2" x2="16" y2="2" />
  </SvgWrapper>
);

const CopperMugIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Moscow mule mug with handle */}
    <path d="M5 5 L5 17 Q5 19 11 19 Q17 19 17 17 L17 5" />
    <line x1="5" y1="5" x2="17" y2="5" />
    <path d="M17 7 Q20 7 20 11 Q20 15 17 15" />
  </SvgWrapper>
);

const PilsnerIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Flared pilsner glass */}
    <path d="M7 3 Q6 12 6 17 Q6 20 12 20 Q18 20 18 17 Q18 12 17 3" />
    <line x1="7" y1="3" x2="17" y2="3" />
  </SvgWrapper>
);

const TikiMugIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Distinctive tiki totem shape */}
    <path d="M7 3 L6 20 L18 20 L17 3 Z" />
    <line x1="7" y1="3" x2="17" y2="3" />
    {/* Tiki face details */}
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
    {/* Elegant hourglass hurricane */}
    <path d="M8 3 Q5 7 7 11 Q5 15 7 19 Q8 20 12 20 Q16 20 17 19 Q19 15 17 11 Q19 7 16 3" />
    <line x1="8" y1="3" x2="16" y2="3" />
  </SvgWrapper>
);

const GobletIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Large rounded goblet bowl */}
    <path d="M6 4 Q4 9 7 13 Q9 15 12 15 Q15 15 17 13 Q20 9 18 4" />
    <line x1="6" y1="4" x2="18" y2="4" />
    <line x1="12" y1="15" x2="12" y2="18" />
    <path d="M8 20 Q12 19 16 20" />
  </SvgWrapper>
);

const PocoGrandeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Curved tulip with stem */}
    <path d="M8 3 Q5 6 7 10 Q5 13 8 15 Q10 16 12 16 Q14 16 16 15 Q19 13 17 10 Q19 6 16 3" />
    <line x1="8" y1="3" x2="16" y2="3" />
    <line x1="12" y1="16" x2="12" y2="18" />
    <path d="M8 20 Q12 19 16 20" />
  </SvgWrapper>
);

const MargaritaIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Classic wide margarita bowl */}
    <path d="M3 5 Q3 7 12 10 Q21 7 21 5" />
    <line x1="3" y1="5" x2="21" y2="5" />
    <line x1="12" y1="10" x2="12" y2="18" />
    <path d="M8 20 Q12 19 16 20" />
  </SvgWrapper>
);

const SnifterIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Brandy snifter - wide belly, narrow top */}
    <path d="M8 4 Q4 8 5 13 Q6 16 12 16 Q18 16 19 13 Q20 8 16 4" />
    <line x1="8" y1="4" x2="16" y2="4" />
    <line x1="12" y1="16" x2="12" y2="19" />
    <path d="M9 21 Q12 20 15 21" />
  </SvgWrapper>
);

const WineGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Classic wine glass silhouette */}
    <path d="M7 4 Q5 8 7 12 Q9 15 12 15 Q15 15 17 12 Q19 8 17 4" />
    <line x1="7" y1="4" x2="17" y2="4" />
    <line x1="12" y1="15" x2="12" y2="19" />
    <path d="M8 21 Q12 20 16 21" />
  </SvgWrapper>
);

const IrishCoffeeIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Footed glass mug */}
    <path d="M6 4 Q5 8 6 13 Q7 15 12 15 Q17 15 18 13 Q19 8 18 4" />
    <line x1="6" y1="4" x2="18" y2="4" />
    <path d="M18 6 Q21 6 21 9 Q21 12 18 12" />
    <line x1="12" y1="15" x2="12" y2="18" />
    <path d="M9 20 Q12 19 15 20" />
  </SvgWrapper>
);

const FizzGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Small narrow fizz glass */}
    <path d="M9 4 L8 19 Q8 20 12 20 Q16 20 16 19 L15 4" />
    <line x1="9" y1="4" x2="15" y2="4" />
  </SvgWrapper>
);

const PunchCupIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Small teacup-style punch cup */}
    <path d="M5 6 Q4 10 6 13 Q8 15 12 15 Q16 15 18 13 Q20 10 19 6" />
    <line x1="5" y1="6" x2="19" y2="6" />
    <path d="M19 8 Q22 8 22 11 Q22 13 19 13" />
  </SvgWrapper>
);

const GlencairnIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Tulip-shaped whisky nosing glass */}
    <path d="M9 4 Q6 7 6 12 Q6 16 12 16 Q18 16 18 12 Q18 7 15 4" />
    <line x1="9" y1="4" x2="15" y2="4" />
    <line x1="12" y1="16" x2="12" y2="19" />
    <path d="M9 21 Q12 20 15 21" />
  </SvgWrapper>
);

const ShotGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    {/* Small tapered shot glass */}
    <path d="M8 8 L9 18 Q9 19 12 19 Q15 19 15 18 L16 8" />
    <line x1="8" y1="8" x2="16" y2="8" />
  </SvgWrapper>
);

// Fallback generic glass
const GenericGlassIcon = (props: SVGProps<SVGSVGElement>) => (
  <SvgWrapper {...props}>
    <path d="M7 4 L8 19 Q8 20 12 20 Q16 20 16 19 L17 4" />
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
