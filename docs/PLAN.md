# Transliteration Plan (Cyrillic to Latin)

## Objective
Fix errors in `Нокис хамме мекемелер.csv` by transliterating all Cyrillic text to the Latin alphabet. Maintain the linguistic integrity by correctly applying Karakalpak Latin rules to Karakalpak text, and Uzbek Latin rules to Uzbek text.

## Approach

1. **Language Detection Strategy**
   - We will write a Python script that reads the CSV.
   - For each organization name, we will detect the language based on common keywords and specific characters:
     - **Karakalpak Markers**: "Қарақалпақстан", "Нөкис", "бөлими", "орайы", "министрлиги", "ҳәм", "хызмети", "мәкемеси", "мәкән", "аўыл", "жәмийети", "кәрханасы".
     - **Uzbek Markers**: "Қорақалпоғистон", "Нукус", "бўлими", "маркази", "вазирлиги", "ва", "хизмати", "муассасаси", "маҳалла", "қишлоқ", "жамияти", "корхонаси".
   - Specific character markers:
     - Characters like `ө`, `ү`, `ң`, `ә`, `ў` (pronounced as 'w') indicate **Karakalpak**.
     - Characters like `ў` (pronounced as 'o''), and absence of Karakalpak-specific letters indicate **Uzbek**.

2. **Transliteration Rules**
   - **Karakalpak**: Map Cyrillic to Latin using the latest Karakalpak Latin alphabet:
     - `ғ` -> `ǵ`
     - `ў` -> `w`
     - `ң` -> `ń`
     - `ө` -> `ó`
     - `ү` -> `ú`
     - `ә` -> `á`
     - `қ` -> `q`
     - `и` -> `i` / `ı` (context-dependent, simplified to standard `i`/`ı` rules or basic `i`)
   - **Uzbek**: Map Cyrillic to Latin using the standard Uzbek Latin alphabet:
     - `ғ` -> `g'`
     - `ў` -> `o'`
     - `қ` -> `q`
     - `ҳ` -> `h`
     - `ч` -> `ch`
     - `ш` -> `sh`
     - `я` -> `ya`
     - `ю` -> `yu`
     - `ц` -> `ts`

3. **Execution Steps**
   - **Step 1:** Orchestrator (project-planner mode) creates `docs/PLAN.md` and gets user approval. *(We are here)*
   - **Step 2 (Implementation):** `backend-specialist` agent will develop and execute a Python script (`transliterate_csv.py`) that applies the logic to `Нокис хамме мекемелер.csv`.
   - **Step 3 (Review):** `database-architect` or `test-engineer` agent will verify the resulting CSV, ensuring data integrity (columns are intact, no Cyrillic chars left, correct mappings applied).
   - **Step 4 (Completion):** Provide the final cleaned CSV file to the user.
