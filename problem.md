<details>
<summary><strong>TASK DETAILS - Only open when you're ready to start the assignment</strong> (click to expand)</summary>

## 📖 The Story

Imagine you are building an **AI-powered brand protection platform**.

The platform helps companies detect **lookalike or impersonation websites** that may:
- Confuse users
- Misuse brand assets (logos, products)
- Impersonate executives or public figures
- Sell counterfeit or misleading products

### Example

- Legitimate domain: `nike.com`
- Lookalike domain: `mynikeshoes.com`

If `mynikeshoes.com`:
- Uses Nike logos
- Mentions Nike executives
- Sells shoes branded as Nike  
…and does **not** belong to Nike, then Nike would want to:
- Be alerted
- Potentially initiate a takedown


## 🚧 The Current Problem

### Customer Onboarding

Today, onboarding requires significant **manual input** from customers.

Your task is to design and prototype a system that **automates onboarding as much as possible**, given minimal initial input.

> With just a few inputs, can we automatically discover and infer most of the relevant information needed for brand protection?

### 🔢 Manual Input (Starting Point)

Assume the customer provides **only**:

- **Company name** (e.g. "Nike")
- **One or more official domains** (e.g. `nike.com`)

### 📉 Today’s Manual Work (What We Want to Reduce)

Currently, customers may need to manually provide:

- Brand / product logos (**images**)
- A list of domains they own
- Keywords related to their business
- Names and faces of key people (e.g. CEO, founders, public figures) (**images**)

Your solution should aim to **automate or infer as much of this as possible**.

## 🧠 Your Task

Design and implement a **working prototype** that:

1. **Takes minimal manual input**
   - Company name
   - One or more official domains

2. **Automatically discovers or infers relevant brand signals**, such as:
   - Additional owned domains
   - Brand logos or visual assets
   - Business keywords or product categories
   - Key people associated with the company (names, faces, roles)
   - Any other signals you think are useful

You're provided an OpenAI API key to use in this assignment.

</details>

## 📦 Deliverables

Please include:

- A working prototype with code
   - Language and tools of your choice
- A clear way to run it
   - `how_to_run.md`
- An analysis of your work
   - How much time spent
   - What you automated
   - What you assumed
   - Trade-offs you made
- TODOs / Next steps
   - What you would improve with more time

## ⏱️ Time Expectation

**3 - 4 hours** continously. We recommend:
- ~3 hours to build a working prototype
- ~1 hour to document and reflect (README, analysis, TODOs)
- However, if you need to pause for more urgent things, feel free to do so.

## ❓ Questions

If anything is unclear, make reasonable assumptions and document them. If anything is vague, it might be intentional! There is no single "correct" solution.