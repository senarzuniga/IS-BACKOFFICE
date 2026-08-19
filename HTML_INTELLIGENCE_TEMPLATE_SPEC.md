# HTML Intelligence: especificacion de plantilla corporativa

## Proposito

Esta especificacion deriva un sistema reutilizable del informe `PCG_MIDDLETOWN_CONVERTING_AUDIT_2026-08-17.html` y de `calgary_report_theme.css`. PCG es la referencia de calidad y composicion, no una fuente de contenido generico. Nombres, cifras, equipos, imagenes, afirmaciones y datos del cliente no se copian a nuevos documentos.

El estandar se aplica por defecto a informes profesionales generados para AI-FACTORY y Adaptive Sales Engine. INGESITE utiliza su identidad visual nativa salvo seleccion humana expresa de otro perfil.

## Principios

1. **Primero decision**: cada informe abre con la decision, el riesgo o la oportunidad que debe resolver.
2. **Contenido trazable**: hechos, hipotesis, propuestas y elementos pendientes se distinguen visual y semanticamente.
3. **Un modelo, dos idiomas**: EN y ES derivan de las mismas unidades semanticas; no son documentos editados por separado.
4. **Multiformato real**: HTML, PDF y DOCX comparten jerarquia y datos, pero cada renderer compone segun su medio.
5. **Legibilidad industrial**: tablas, formulas, flujos, KPIs y gates prevalecen sobre decoracion.
6. **Entrega reproducible**: cada salida declara version, idioma, perfil, hashes y validaciones.

## Anatomia obligatoria

### 1. Cabecera hero

- Imagen relevante a pantalla completa con overlay oscuro; debe mostrar el producto, planta, proceso o contexto real.
- Eyebrow: cliente, ubicacion, dominio o proyecto.
- Marca y logo con texto alternativo.
- H1 literal, orientado a decision, sin lenguaje promocional generico.
- Parrafo de alcance de una o dos frases.
- Metadata visible: tipo de informe, fecha ISO, idioma, version y estado.
- Borde inferior naranja como firma del perfil PCG.

### 2. Ribbon de decision

- Banda compacta con una etiqueta principal y entre tres y siete dimensiones del analisis.
- Las dimensiones proceden del modelo y sirven como indice ejecutivo, no como keywords decorativas.

### 3. Navegacion y contenido

- Tabla de contenidos lateral sticky en desktop.
- Navegacion oculta o colapsada en tablet/mobile sin bloquear lectura.
- Secciones numeradas con `section_no`, titulo, resumen opcional y componentes.
- Anchura maxima de contenido: 1240 px; rail lateral de aproximadamente 250 px.

### 4. Cierre

- Evidencia, fuentes, limitaciones y disclaimers.
- Identidad de version, fecha de generacion y referencia al manifiesto.
- Informacion de contacto solo cuando el perfil de entrega lo permita.

## Sistema visual PCG generalizado

### Tokens

| Token | Valor de referencia | Uso |
|---|---|---|
| `ink` | `#181817` | Texto principal |
| `paper` | `#f2efe8` | Fondo impreso/editorial |
| `surface` | `#ffffff` | Tablas, decisiones y componentes |
| `line` | `#d2cbc0` | Bordes y separadores |
| `muted` | `#625f59` | Metadata y texto secundario |
| `orange` | `#ff5a10` | Identidad y accion principal |
| `orange_dark` | `#a94400` | Titulos auxiliares accesibles |
| `green` | `#14735f` | Hecho validado o resultado positivo |
| `amber` | `#8b6700` | Propuesta, cautela o pendiente |
| `red` | `#9f3232` | Riesgo o incumplimiento |
| `black` | `#0c0c0c` | Hero, ribbon y encabezados de tabla |

Los perfiles de cliente pueden sustituir marca y acento siempre que mantengan contraste WCAG AA y la semantica de estados no dependa solo del color.

### Tipografia

- Titulares: familia serif editorial equivalente a Georgia, peso 800.
- Cuerpo: Aptos o Segoe UI; fallback sans-serif.
- Metadata, etiquetas, formulas y numeros tecnicos: Cascadia Mono o Consolas.
- Letter spacing: `0` para texto normal; solo eyebrow/tag puede usar tracking positivo moderado.
- El renderer DOCX utiliza estilos nombrados equivalentes; no simula jerarquia con formato directo.

### Espaciado y geometria

- Unidad base: 4 px; componentes usan multiplos de 4.
- Cards: radio maximo 6 px en el perfil PCG.
- No se anidan cards dentro de cards.
- Las tablas se presentan en contenedores de overflow horizontal en HTML.
- KPIs tienen altura estable y grid responsive 4/2/1 columnas.
- Diagramas de flujo usan tracks estables y pasan a una columna en pantallas estrechas.

## Componentes semanticos

| Componente | Campos minimos | Reglas de renderizado |
|---|---|---|
| `decision` | titulo, cuerpo, estado | Borde izquierdo, superficie blanca, estado textual |
| `kpi_grid` | label, value, detail, evidence | 2-4 columnas; valor y unidad inseparables |
| `evidence_badge` | clase, label, source_ref | Clases `client`, `verify`, `audit`, `derived` |
| `risk_card` | riesgo, impacto, mitigacion | Estado rojo/ambar y texto explicito |
| `comparison_table` | headers, rows, units | Header oscuro, filas no partidas en PDF si caben |
| `formula` | expresion, variables, disclaimer | Monospace; nunca se traduce el simbolismo |
| `process_flow` | pasos, enlaces, control_points | Grid en HTML; equivalente accesible en DOCX/PDF |
| `phase` | nombre, objetivo, actividades, salida | Secuencia numerada y borde de acento |
| `gate` | criterio, owner, estado, evidencia | Estado y decision requerida obligatorios |
| `source_list` | id, titulo, ubicacion, fecha, hash | Referencias estables al manifiesto |

Los componentes DIPC existentes se reutilizan cuando su semantica coincide. Las variantes visuales pertenecen al theme/renderer, no al contenido.

## Evidencia y gobernanza

Clases corporativas:

- `client`: informacion proporcionada por cliente o sistema fuente.
- `verify`: afirmacion pendiente de medicion, placa, historico o aprobacion.
- `audit`: hallazgo confirmado por auditoria o analisis.
- `derived`: calculo reproducible a partir de fuentes declaradas.

Cada hecho relevante debe enlazar con un `EvidenceRecord` que incluya `source_ref`, descripcion, timestamp cuando exista, confianza y metadata de unidad. Las afirmaciones sin evidencia se etiquetan; no se presentan como garantias.

## Bilinguismo EN/ES

### Modelo

- Cada unidad traducible tiene clave estable y valores `en` y `es`.
- El idioma de origen queda registrado.
- Nombres propios, referencias, codigos, valores, formulas y unidades se bloquean mediante placeholders durante traduccion.
- El glosario define terminos preferidos y terminos que no deben traducirse.
- La validacion compara estructura, conteo de componentes, cifras, unidades, enlaces y evidencia entre idiomas.

### HTML

- Puede entregarse un HTML bilingue con selector accesible o un HTML por idioma segun perfil.
- El selector usa botones, `aria-pressed` y atributo `lang` actualizado.
- Todo el contenido, incluyendo TOC, secciones, tablas, labels, alt text y disclaimers, cambia de idioma.
- Sin JavaScript, el idioma principal permanece visible y legible.

### PDF y DOCX

- Cada archivo tiene un solo idioma salvo que el perfil solicite edicion bilingue paralela.
- El idioma se incorpora al nombre: `{document_id}_{version}_{language}.{format}`.
- Propiedades del documento, estilos y texto alternativo declaran el idioma correspondiente.

## Reglas por formato

### HTML

- HTML5 semantico, headings en orden, landmarks y enlaces internos.
- CSS externo empaquetado; assets locales con hashes y rutas portables.
- Responsive en 1440, 1024, 768 y 390 px.
- Sin dependencias de red obligatorias para abrir el paquete entregable.

### PDF

- A4 por defecto; Letter por perfil de cliente.
- Portada/hero controlada, margenes, encabezado/pie y numeracion.
- `break-inside: avoid` para decisiones, cards y filas cortas.
- Tablas anchas se adaptan, rotan o dividen de forma intencional; nunca se recortan silenciosamente.
- Fuentes y assets deben estar incrustados o disponibles localmente.

### DOCX

- Estilos corporativos para Title, Heading 1-3, Body, Caption, Table y Evidence.
- Tabla de contenidos actualizable, saltos de seccion y headers/footers.
- Tablas nativas, imagenes con alt text y propiedades de idioma.
- No se usa HTML pegado como sustituto del modelado Word.

### XLSX

- Solo se genera cuando el modelo contiene datos tabulares o calculos reutilizables.
- Hojas sugeridas: `Summary`, tablas por dominio, `Sources`, `Validation` y `Manifest`.
- Unidades y formatos numericos explicitos; formulas preservadas y celdas de entrada diferenciadas.
- No se fuerza una narrativa larga a una hoja de calculo.

### PPTX

- Solo se genera para contenido apto para presentacion.
- Una idea principal por slide; tablas densas se resumen y enlazan al anexo.
- Master corporativo, notas de fuente y speaker notes cuando proceda.
- Graficos y diagramas se construyen como objetos editables cuando sea razonable.

## Perfiles visuales

| Perfil | Aplicacion | Regla |
|---|---|---|
| `pcg_corporate` | AI Factory, ASE e informes generales | Estructura y tokens de esta especificacion |
| `ingecart_industrial` | Informes tecnicos ya soportados por HIS | Compatible con DIPC, seleccion explicita |
| `ingesite_native` | Paginas/derivados destinados a INGESITE | Conserva `css/styles.css`, Inter/Poppins y paleta nativa |
| `client_custom` | Entregas con brand pack aprobado | Extiende un perfil base; no altera semantica/evidencia |

## Perfil de entrega Cascades inicial

- Formato permitido: PDF exclusivamente.
- Idioma y tamano de pagina: definidos en el perfil de cliente.
- El paquete contiene PDF, `manifest.json`, `validation_report.json` y checksums.
- HTML, DOCX, fuentes editables y fuentes originales no se incluyen.
- La validacion de paquete falla si aparece una extension no permitida.

## Validaciones obligatorias

1. Esquema del modelo y envolvente corporativa validos.
2. Identidad, version, idioma, cliente, fuente y destino presentes.
3. Paridad EN/ES de estructura, numeros, unidades, nombres y evidencia.
4. Sin enlaces ni assets rotos; todos los assets de entrega son portables.
5. Jerarquia de headings, alt text, contraste y landmarks accesibles.
6. Sin overflow, solapes o contenido cortado en viewports objetivo.
7. PDF/DOCX abren correctamente y contienen contenido no vacio.
8. Dependencias coinciden con los hashes registrados; en caso contrario, estado `stale`.
9. Formatos generados y empaquetados respetan el perfil del cliente.
10. La raiz INGESITE y sus originales conservan sus hashes tras cualquier mision.

## Convencion de salida

```text
{output_root}/
  {client_slug}/
    {document_id}/
      v{major}.{minor}.{patch}/
        model/
        sources/
        en/
        es/
        packages/
        validation/
        manifest.json
```

El manifiesto raiz enlaza artefactos por idioma/formato, dependencias, hashes, perfil visual, perfil de entrega, validaciones, timestamps y estado de publicacion.

## Criterio de conformidad PCG

Una salida es conforme cuando conserva la anatomia, jerarquia, semantica de evidencia, legibilidad industrial, comportamiento responsive/print y calidad de entrega de la referencia, sin reutilizar datos particulares de PCG. La similitud visual por si sola no es suficiente: deben cumplirse trazabilidad, bilingüismo, accesibilidad, versionado y restricciones de entrega.
