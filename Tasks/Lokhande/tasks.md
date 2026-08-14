## Phase 6 — GenAI Personalization ⭐

Now bring the LLM into the system.

The ML engine decides:
**WHAT to offer**

GenAI decides:
**HOW to communicate it**

### Input

**Customer:**
- Frequent traveller

**Recent event:**
- Flight purchase

**Recommended product:**
- Travel Credit Card

**Reasons:**
- High travel spending
- No suitable travel card
- Eligible

### GenAI output
> "Planning your next journey?
> Explore our travel-focused credit card
> and its eligible travel benefits."

**Generate:**
- Push notification
- Email
- SMS
- In-app message
- Relationship-manager script

### Important architecture

Don't let the LLM invent product details.

**Use:**
```text
Product Catalogue
      ↓
Approved Benefits
      ↓
LLM
      ↓
Marketing Message
```

---

## Phase 7 — Marketing Campaign Engine

Now convert recommendations into actual campaigns.

### Campaign Creation

**Employee selects:**

**Product:**
Travel Credit Card

**Target:**
Frequent Travellers

**Trigger:**
Recent flight transaction

**Minimum propensity:**
70%

**System selects customers:**

```text
1,000,000 customers
       ↓
Travel customers
       ↓
Eligible customers
       ↓
Propensity > 70%
       ↓
Target audience
```