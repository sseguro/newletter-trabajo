# Notas editoriales — VTC Weekly

Ajustes de feedback aplicados en la edición del 22 de septiembre de 2026, válidos para ediciones futuras salvo indicación contraria:

1. **Título visible (H1) simplificado.** No usar "VTC Weekly — Señales de cambio" como titular grande del cuerpo de la newsletter. Usar solo **"Señales del cambio"**. El eyebrow superior ("VIGILANCIA TECNOLÓGICA COMPETITIVA") se mantiene. El formato largo "VTC Weekly — Señales de cambio · Semana N · fecha" se conserva únicamente como **asunto del email**.
2. **Línea de metadatos simplificada.** No incluir la cláusula "· cubre X–Y sep (backlog de N semanas)" en la línea de fecha bajo el título. Dejar solo "Semana N · fecha". Si hay backlog que explicar, mencionarlo en el resumen ejecutivo, no en la cabecera.
3. **El gráfico de evolución NUNCA debe embeberse como `<svg>` inline en el `htmlBody` de un borrador de Gmail.** Gmail elimina las etiquetas `<svg>`/`<path>`/`<rect>` de su sanitizador de HTML pero conserva sueltos los nodos de texto internos (`<text>`), lo que deja un párrafo de texto suelto con todas las etiquetas del gráfico y ningún dibujo. Usar siempre una **imagen rasterizada (PNG)** referenciada por `<img src="...">`.
   - Preferir una **URL externa estable** (ej. `raw.githubusercontent.com/<owner>/<repo>/<commit_sha>/<path>` sobre el commit ya empujado al repo) en lugar de `data:` URI en base64. Motivo práctico: el base64 de una imagen de este tamaño (~40–200KB) se tokeniza muy mal (~2 tokens/carácter) y hace inviable leerlo de vuelta al contexto para construir la llamada a la herramienta de Gmail. Una URL externa mantiene el HTML del correo por debajo de ~30KB.
   - Si se usa URL externa, verificar primero que el repo es público (`curl -I` a la raw URL debe devolver 200) y anclar la URL al **commit SHA**, no a la rama, para que no cambie si la rama se sigue actualizando.
4. **Verificar el borrador tras crearlo.** El `draftId` devuelto por `create_draft` puede dejar de ser válido (el borrador puede desaparecer del buzón, por ejemplo si se abrió con una herramienta externa para generar una captura/PDF de revisión). Antes de intentar `update_draft`, o si se recibe el error "Message not a draft", comprobar con `list_drafts` y, si no existe, crear uno nuevo en lugar de reintentar la actualización.

## Fuente de datos

- Las observaciones "VTC" viven en Airtable, tabla "VTC" (mismo esquema en dos bases): `futuro-trabajo` (histórico acumulado) y `futuro-trabajo-2` (bandeja de entrada más reciente, aún sin fusionar). Antes de cada edición, comprobar el rango de IDs/fechas en ambas bases para detectar backlog sin sintetizar.
- La memoria narrativa previa (síntesis semanales anteriores a este formato estructurado) vive en Notion, página "VTC", hijos "Síntesis prospectiva VTC — [rango de fechas]".
- El registro estructurado de señales (FASE 0, con historial_fuerza) vive en este repo: `newsletters/<fecha>/signal-registry.json`. Cada edición nueva debe leer el registro de la edición anterior antes de crear el suyo, para mantener IDs de señal estables (S-01, S-02, ... y SD-01, SD-02, ...).
