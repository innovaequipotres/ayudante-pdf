const literatureContent = `Unidad 3: Lectura y análisis de un cuento de Horacio Quiroga. Lean el cuento indicado en clase y registren los momentos que modifican el rumbo de la historia. El narrador relata los sucesos desde una perspectiva omnisciente que permite al lector reconstruir el sentido subyacente del cuento. Observen cómo el ambiente y las decisiones de los personajes contribuyen al desenlace. En grupos, realicen un análisis exhaustivo de los recursos narrativos y expongan sus conclusiones ante el curso. Para organizar el trabajo, cada integrante puede proponer una interpretación y luego comparar las evidencias del texto.`;

const biologyContent = `La mitosis es el proceso de división celular mediante el cual una célula eucariota origina dos células hijas con información genética equivalente. Antes de comenzar, el ADN se duplica para que cada célula nueva reciba una copia completa. Durante la profase, los cromosomas se condensan y se forma el huso mitótico. En la metafase, los cromosomas se alinean en el centro de la célula. La ilustración representa las fibras del huso con un tono azul claro sobre un fondo también claro. Durante la anafase, las cromátidas hermanas se separan y se desplazan hacia polos opuestos. Por último, la telofase reorganiza los núcleos y la citocinesis divide el citoplasma. Respondé las siguientes preguntas: ¿Qué ocurre con el ADN antes de la mitosis? ¿En qué fase se alinean los cromosomas? ¿Qué función cumple el huso mitótico? Explicá con tus palabras por qué las células hijas conservan la información genética de la célula original.`;

const geographyContent = `Europa es un continente de superficie relativamente reducida en comparación con Asia, pero presenta una gran variedad de formas del relieve, climas, paisajes y ambientes. Sus límites convencionales se reconocen al este en los montes Urales y el río Ural, al sur en el mar Mediterráneo y al oeste en el océano Atlántico, aunque las relaciones históricas y culturales entre Europa y Asia hacen que la división entre ambos continentes también sea una construcción geográfica. El relieve europeo se organiza en grandes unidades que incluyen macizos antiguos, extensas llanuras y cordilleras jóvenes, entre ellas los Alpes, los Pirineos y los Cárpatos. Las llanuras se extienden desde el oeste hacia el este y facilitan la circulación, la agricultura y el asentamiento de numerosas poblaciones, mientras que las áreas montañosas influyen en las comunicaciones y en la distribución de los cursos de agua. La diversidad de costas, penínsulas e islas genera una extensa relación con el mar y favorece la existencia de ambientes litorales diferentes. El clima varía desde las condiciones oceánicas húmedas del oeste hasta los rasgos continentales del interior y los ambientes mediterráneos del sur, donde los veranos suelen ser secos y los inviernos más moderados. En el norte, la latitud y la influencia de las corrientes marinas producen temperaturas más bajas, mientras que la altitud modifica las condiciones en las zonas montañosas. Los ríos cumplen funciones importantes para el abastecimiento, la producción de energía, el transporte y el desarrollo de ecosistemas, aunque sus caudales dependen del clima, el relieve y las actividades humanas. La vegetación natural incluye bosques templados, formaciones mediterráneas, praderas y ambientes de tundra, pero fue transformada durante siglos por la expansión urbana, la agricultura, la industria y la construcción de infraestructura. En la actualidad, la contaminación del aire y del agua, la pérdida de biodiversidad, los incendios y el cambio climático afectan de manera desigual a las distintas regiones. Para comprender la configuración física y ambiental de Europa es necesario relacionar sus componentes naturales con la historia de ocupación del territorio y con las decisiones que toman las sociedades para utilizar y proteger sus recursos.`;

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
          "La ilustración representa las fibras del huso con un tono azul claro sobre un fondo también claro.",
        suggestion:
          "La ilustración representa las fibras del huso con un tono azul oscuro sobre un fondo claro.",
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
