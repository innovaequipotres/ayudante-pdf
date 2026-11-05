const literatureContent = `
<h1>Unidad 3: Lectura y análisis de un cuento de Horacio Quiroga</h1>
<p>Lean el cuento indicado en clase y registren los momentos que modifican el rumbo de la historia.</p>
<h2>El narrador y el ambiente</h2>
<p>El narrador relata los sucesos desde una perspectiva omnisciente que permite al lector reconstruir el sentido subyacente del cuento. Observen cómo el ambiente y las decisiones de los personajes contribuyen al desenlace.</p>
<h2>Trabajo grupal</h2>
<p>En grupos, realicen un análisis exhaustivo de los recursos narrativos y expongan sus conclusiones ante el curso. Para organizar el trabajo, cada integrante puede proponer una interpretación y luego comparar las evidencias del texto.</p>`;

const biologyContent = `
<h1>La mitosis</h1>
<p>La mitosis es el proceso de división celular mediante el cual una célula eucariota origina dos células hijas con información genética equivalente. Antes de comenzar, el ADN se duplica para que cada célula nueva reciba una copia completa.</p>
<figure>
  <img src="/demo-pdfs/Examen_Biologia_Celula_figura.png" alt="Diagrama de una célula con el núcleo y la membrana identificados." />
  <figcaption>Partes principales de una célula.</figcaption>
</figure>
<p>La figura muestra la célula con el núcleo en un tono azul claro sobre un fondo también claro.</p>
<h2>Etapas de la mitosis</h2>
<p>Durante la profase, los cromosomas se condensan y se forma el huso mitótico. En la metafase, los cromosomas se alinean en el centro de la célula. Durante la anafase, las cromátidas hermanas se separan y se desplazan hacia polos opuestos. Por último, la telofase reorganiza los núcleos y la citocinesis divide el citoplasma.</p>
<h2>Preguntas</h2>
<p>Respondé las siguientes preguntas:</p>
<ol>
  <li>¿Qué ocurre con el ADN antes de la mitosis?</li>
  <li>¿En qué fase se alinean los cromosomas?</li>
  <li>¿Qué función cumple el huso mitótico?</li>
  <li>Explicá con tus palabras por qué las células hijas conservan la información genética de la célula original.</li>
</ol>`;

const geographyContent = `
<h1>Europa: relieve, climas y ambientes</h1>
<p>Europa es un continente de superficie relativamente reducida en comparación con Asia, pero presenta una gran variedad de formas del relieve, climas, paisajes y ambientes. Sus límites convencionales se reconocen al este en los montes Urales y el río Ural, al sur en el mar Mediterráneo y al oeste en el océano Atlántico, aunque las relaciones históricas y culturales entre Europa y Asia hacen que la división entre ambos continentes también sea una construcción geográfica.</p>
<h2>Relieve europeo</h2>
<p>El relieve europeo se organiza en grandes unidades que incluyen macizos antiguos, extensas llanuras y cordilleras jóvenes, entre ellas los Alpes, los Pirineos y los Cárpatos. Las llanuras se extienden desde el oeste hacia el este y facilitan la circulación, la agricultura y el asentamiento de numerosas poblaciones, mientras que las áreas montañosas influyen en las comunicaciones y en la distribución de los cursos de agua.</p>
<figure>
  <img src="/demo-pdfs/TP_Geografia_Europa_relieve.png" alt="Esquema de formas del relieve representadas con figuras geométricas de distintos colores." />
  <figcaption>Representación esquemática de distintas formas del relieve.</figcaption>
</figure>
<p>La diversidad de costas, penínsulas e islas genera una extensa relación con el mar y favorece la existencia de ambientes litorales diferentes. El clima varía desde las condiciones oceánicas húmedas del oeste hasta los rasgos continentales del interior y los ambientes mediterráneos del sur, donde los veranos suelen ser secos y los inviernos más moderados. En el norte, la latitud y la influencia de las corrientes marinas producen temperaturas más bajas, mientras que la altitud modifica las condiciones en las zonas montañosas.</p>
<figure>
  <img src="/demo-pdfs/TP_Geografia_Europa_mapa.png" alt="Mapa temático de Europa con regiones representadas en tonos verdes y ocres." />
  <figcaption>Mapa temático de regiones europeas.</figcaption>
</figure>
<h2>Ambientes y sociedades</h2>
<p>Los ríos cumplen funciones importantes para el abastecimiento, la producción de energía, el transporte y el desarrollo de ecosistemas, aunque sus caudales dependen del clima, el relieve y las actividades humanas.</p>
<p>La vegetación natural incluye bosques templados, formaciones mediterráneas, praderas y ambientes de tundra, pero fue transformada durante siglos por la expansión urbana, la agricultura, la industria y la construcción de infraestructura. En la actualidad, la contaminación del aire y del agua, la pérdida de biodiversidad, los incendios y el cambio climático afectan de manera desigual a las distintas regiones.</p>
<p>Para comprender la configuración física y ambiental de Europa es necesario relacionar sus componentes naturales con la historia de ocupación del territorio y con las decisiones que toman las sociedades para utilizar y proteger sus recursos.</p>`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const DEMO_MOCKS: Record<string, any> = {
  "Guia_Literatura_Unidad3.pdf": {
    id: "demo-guia-literatura-unidad3",
    name: "Guia_Literatura_Unidad3.pdf",
    size: "1,6 MB",
    originalContent: literatureContent,
    modifiedContent: literatureContent,
    barriers: [
      {
        id: "literatura-perspectiva-narrativa",
        severity: "Media",
        category: "Claridad del lenguaje",
        original:
          "El narrador relata los sucesos desde una perspectiva omnisciente que permite al lector reconstruir el sentido subyacente del cuento.",
        suggestion:
          "Quien cuenta la historia conoce lo que piensan y sienten los personajes. Esto ayuda a comprender el sentido del cuento.",
      },
      {
        id: "literatura-consigna-grupal",
        severity: "Alta",
        category: "Claridad de la consigna",
        original:
          "En grupos, realicen un análisis exhaustivo de los recursos narrativos y expongan sus conclusiones ante el curso.",
        suggestion:
          "En grupos, identifiquen los recursos narrativos del cuento y compartan sus conclusiones con el curso.",
      },
    ],
  },
  "Examen_Biologia_Celula.pdf": {
    id: "demo-examen-biologia-celula",
    name: "Examen_Biologia_Celula.pdf",
    size: "2,1 MB",
    originalContent: biologyContent,
    modifiedContent: biologyContent,
    barriers: [
      {
        id: "biologia-contraste-ilustracion",
        severity: "Alta",
        category: "Contraste visual",
        original:
          "La figura muestra la célula con el núcleo en un tono azul claro sobre un fondo también claro.",
        suggestion:
          "La figura muestra la célula con el núcleo en un tono azul oscuro sobre un fondo claro.",
      },
      {
        id: "biologia-vocabulario-mitosis",
        severity: "Media",
        category: "Claridad del lenguaje",
        original:
          "La mitosis es el proceso de división celular mediante el cual una célula eucariota origina dos células hijas con información genética equivalente.",
        suggestion:
          "La mitosis es el proceso por el que una célula eucariota se divide y forma dos células nuevas con la misma información genética.",
      },
      {
        id: "biologia-preguntas-examen",
        severity: "Baja",
        category: "Estructura de las preguntas",
        original:
          "Respondé las siguientes preguntas: ¿Qué ocurre con el ADN antes de la mitosis? ¿En qué fase se alinean los cromosomas? ¿Qué función cumple el huso mitótico?",
        suggestion:
          "Respondé estas preguntas por separado:\n1. ¿Qué ocurre con el ADN antes de la mitosis?\n2. ¿En qué fase se alinean los cromosomas?\n3. ¿Qué función cumple el huso mitótico?",
      },
    ],
  },
  "TP_Geografia_Europa.pdf": {
    id: "demo-tp-geografia-europa",
    name: "TP_Geografia_Europa.pdf",
    size: "3,4 MB",
    originalContent: geographyContent,
    modifiedContent: geographyContent,
    barriers: [
      {
        id: "geografia-carga-relieve",
        severity: "Alta",
        category: "Carga cognitiva",
        original:
          "El relieve europeo se organiza en grandes unidades que incluyen macizos antiguos, extensas llanuras y cordilleras jóvenes, entre ellas los Alpes, los Pirineos y los Cárpatos.",
        suggestion:
          "El relieve europeo tiene tres grandes unidades: macizos antiguos, llanuras y cordilleras jóvenes. Los Alpes, los Pirineos y los Cárpatos son ejemplos de estas cordilleras.",
      },
      {
        id: "geografia-vocabulario-ambientes",
        severity: "Media",
        category: "Claridad del lenguaje",
        original:
          "La vegetación natural incluye bosques templados, formaciones mediterráneas, praderas y ambientes de tundra, pero fue transformada durante siglos por la expansión urbana, la agricultura, la industria y la construcción de infraestructura.",
        suggestion:
          "La vegetación natural incluye bosques templados, vegetación mediterránea, praderas y tundra. Durante siglos, las ciudades, la agricultura, la industria y las obras modificaron estos ambientes.",
      },
      {
        id: "geografia-relacion-ambiente-sociedad",
        severity: "Baja",
        category: "Organización de la información",
        original:
          "Para comprender la configuración física y ambiental de Europa es necesario relacionar sus componentes naturales con la historia de ocupación del territorio y con las decisiones que toman las sociedades para utilizar y proteger sus recursos.",
        suggestion:
          "Para comprender Europa, relacioná sus componentes naturales con la historia de ocupación del territorio. También analizá cómo las sociedades usan y protegen sus recursos.",
      },
    ],
  },
};
