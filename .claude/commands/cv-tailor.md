Re-generate a tailored CV for a specific job posting.

## Instructions

1. Read the user's master CV:
```bash
cat "Full CV.md"
```

2. If the user provides a job URL, first evaluate it via `/eval` to get the scoring and archetype match

3. Based on the evaluation, determine the best archetype:
   - **Product Designer / UX Lead** — emphasize Lowe's, Verbosity, Visa, design systems
   - **IoT Systems Engineer** — emphasize StructureSense, LoRaWAN, RTLS, BLE, DMX512
   - **Creative Technologist** — emphasize Bezant Solutions, 3D printing, firmware, AI workflows
   - **Front-End / Web Developer** — emphasize BancVue, Gensuite, Harland Clarke
   - **Design Systems / UX Architect** — emphasize Visa atomic design, Harland Clarke, Lowe's Digital

4. Generate a tailored CV that:
   - Reorders experience sections by relevance to the role
   - Emphasizes matching skills and keywords from the JD
   - Adjusts the professional summary for the archetype
   - Never fabricates experience — only reframes and reorders

5. Output as clean markdown that can be converted to HTML/PDF

## Input
- `$ARGUMENTS`: A job URL or job ID to tailor the CV for
