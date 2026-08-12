**Task 1: Upload → Postgres**

We've attached the `data_pack.zip` archive — it contains an export from our internal API: files `page_001.json` … `page_020.json`, ~1000 companies
(name, category, city, address, rating, number of reviews, website, phone). The format is as-is, no documentation: figure out the structure yourself.

– Fetch all records from all pages  
– Design a schema and load the data into PostgreSQL (Docker or free-tier Supabase): deduplication, indexes.  
– Provide 3 SQL queries: top‑5 categories by number of companies; average rating by city among companies with 10+ reviews; share of companies with a website per category.  
– Deliverable: a repository with the load script, `schema.sql`, `queries.sql` and a README with the startup command.

---

**Task 2: Mini‑feature with proof of work**

A small page in Next.js (App Router) on top of the database from Task 1:

– Route `/companies`: a table of companies from Postgres with search by name and filter by city.  
– Pull data server‑side (Route Handler or Server Component), no secrets in the repository — only `.env.example`.

**Tooling**

Claude Code / Cursor / Codex / Kimi code

– Provide evidence that everything works: screenshots of the page + 3–5 sentences describing how you tested it yourself (what you clicked, what broke along the way). The "how I tested" part is mandatory.

---

**Task 3: Data with a surprise**

The same archive also contains `review.csv` — allegedly a fresh export for the same database. Load it with a script and give a short data report. But stay alert: maybe we mixed something up…

– List anything odd you notice in `ANOMALIES.md` — what exactly is wrong and how you discovered it.

---

**Task 4: Vibecoding / LLM stack**

In your own words, without AI help. The more specific, the better.

– Your choice of IDE and LLM models now, and how that has changed over the last six months.  
– How many and which subscriptions per month are enough for you to work productively.  
– How do you compare two new models or tools — by feel or on the same set of tasks?  
– What tests would you require for a new feature?  
– What permissions would you give to a coding agent that has access to the terminal and database?  
– Do you write automated tests and include them in CI/CD? What checks must absolutely pass before merging and deployment?