# 🛒 Supermarket Ops Agent

A Telegram-first AI agent for operating an Indian kirana/supermarket through natural language.

The **Supermarket Ops Agent** allows a store owner to manage inventory, billing, GST, customer Khata/credit, sales analytics, documents, and persistent store preferences directly through Telegram.

The system uses **Google Agent Development Kit (ADK)** with **Gemini** for natural-language reasoning and tool orchestration, while **SQLite** acts as the persistent source of truth for store data.

---

## 🚀 Key Features

### 📦 Inventory Management

* Add supermarket products/SKUs
* Check current stock
* Receive additional stock
* Directly sell/decrement inventory
* Detect low-stock products
* Store:

  * Cost price
  * Selling price
  * MRP
  * Quantity
  * Reorder level
  * GST rate
  * HSN code

### 🧾 Billing

* Create draft bills
* Add multiple products to a bill
* View complete bill details
* Modify item quantities
* Remove items from draft bills
* Finalize sales
* Support:

  * Cash
  * UPI
  * Card
* Store payment references
* Handle insufficient and excess payment
* Prevent editing finalized bills

### 📒 Customer Khata / Credit

* Create customers
* Check customer outstanding balance
* Add customer credit
* Record customer payments
* Finalize bills directly against customer Khata
* Automatically update outstanding customer balance

### 🧮 GST

The billing layer calculates GST using the product's stored GST rate.

The system maintains:

* Subtotal
* GST amount
* CGST
* SGST
* Grand total

GST information is calculated by the business layer rather than being invented by the language model.

### 📄 Business Documents

The agent can generate real business artifacts:

* GST invoice PDF
* Daily sales-analysis PowerPoint presentation

Generated files are stored under:

```text
data/invoices/
data/analysis/
```

The Telegram bot automatically sends generated PDF/PPTX files back to the store owner.

### 📊 Sales Analytics

Daily analytics include:

* Number of finalized bills
* Sales subtotal
* GST collected
* CGST
* SGST
* Total sales
* Payment-mode breakdown
* Top-selling products
* Low-stock products

### 🧠 Persistent Store Preferences

Store preferences are saved in SQLite instead of relying only on conversational memory.

Examples:

* Default payment mode
* Preferred product
* Store information
* Other operational preferences

Therefore, conversational context can be reset while persistent store preferences remain available.

---

# 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │       Telegram       │
                    │     Store Owner      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Google ADK       │
                    │       + Gemini       │
                    │                      │
                    │ Observe → Reason     │
                    │ → Act → Observe      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │  Inventory  │  │   Billing   │  │   Khata /   │
       │    Tools    │  │    Tools    │  │  Customer   │
       └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                     ┌──────────────────┐
                     │      SQLite      │
                     │                  │
                     │ Products         │
                     │ Inventory        │
                     │ Bills            │
                     │ Bill Items       │
                     │ Customers        │
                     │ Payments         │
                     │ Preferences      │
                     └────────┬─────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          ┌──────────────┐         ┌──────────────┐
          │ GST Invoice  │         │ Sales PPTX   │
          │     PDF      │         │   Analysis   │
          └──────────────┘         └──────────────┘
```

---

# 🤖 Agent Control Loop

The agent follows the control loop:

**Observe → Reason → Act → Observe → Continue**

The model interprets natural-language requests and selects the appropriate tools.

For example:

> "Make a bill for 2 Maggi and 1 Tata Salt, UPI"

The agent can:

1. Identify the requested products.
2. Check product information and stock.
3. Obtain product IDs from the database.
4. Create a draft bill.
5. Add the requested items.
6. Retrieve calculated bill totals.
7. Apply the requested payment mode.
8. Finalize the transaction.
9. Return the result to the owner.
10. Generate an invoice when requested.

Multiple tools can be composed during a single conversational request.

---

# 🧩 Tool Design

The application uses focused domain tools rather than exposing one large CRUD operation.

## Inventory Tools

Implemented capabilities include:

```text
check_stock
check_low_stock
receive_inventory
sell_inventory
```

The underlying inventory layer provides:

```text
add_product
receive_stock
get_stock
get_low_stock
sell_stock
```

---

## Billing Tools

The billing agent exposes:

```text
create_new_bill
add_item_to_bill
view_bill
change_bill_item
delete_bill_item
complete_bill
complete_credit_bill
```

Additional document generation:

```text
generate_bill_invoice
generate_daily_sales_report
```

---

## Customer / Khata Tools

```text
create_new_customer
check_customer_balance
add_customer_credit
receive_customer_payment
```

---

## Preference / Memory Tools

```text
save_owner_preference
remember_owner_preference
view_owner_preferences
```

These operate on the persistent `owner_preferences` table.

---

# 🔐 Business Rules and Guardrails

A major design principle is:

> **The model decides what operation is required; the business tools decide whether the operation is valid.**

This prevents the language model from becoming the source of truth for financial or inventory information.

## Stock Validation

The inventory layer checks actual stock before selling.

For example:

```text
Available stock = 6
Requested stock = 10

Result:
Transaction rejected
```

The agent cannot simply claim that 10 units were sold.

---

## Draft Bills

Creating or editing a bill does not immediately reduce inventory.

A bill can remain in:

```text
draft
```

while the owner modifies it.

Example:

> "Make a bill with 2 Maggi and 1 butter."

Then:

> "Remove the butter and make Maggi 6."

The draft is updated before finalization.

---

## Finalization

Stock is deducted when a sale is finalized.

The billing layer performs the required validation and database updates rather than relying solely on the prompt.

---

## Payment Validation

Supported payment modes:

```text
cash
upi
card
```

The system handles:

* Insufficient payment
* Exact payment
* Excess payment/change
* Payment references
* Already finalized bills

An insufficient payment does not finalize the transaction.

---

## Credit / Khata Billing

Credit bills use a dedicated finalization flow.

The credit operation:

1. Validates the customer.
2. Validates stock.
3. Deducts stock.
4. Finalizes the bill.
5. Adds the bill total to customer Khata.
6. Updates the outstanding balance.

This avoids separately adding credit after the bill has already been finalized.

---

# 🧮 GST Calculation

GST is calculated inside the billing/business layer.

Each bill item stores relevant product information at billing time:

```text
Product name
Quantity
Unit price
GST rate
GST amount
Line total
```

The bill stores:

```text
Subtotal
GST
CGST
SGST
Total
```

This also helps preserve historical billing information when product data changes later.

---

# 📄 GST Invoice Generation

A finalized bill can be converted into a real PDF GST invoice.

The invoice contains:

* Store heading
* GST invoice title
* Bill number
* Date
* Customer
* Payment mode
* Product details
* Quantity
* Unit price
* GST rate
* GST amount
* Line total
* Subtotal
* CGST
* SGST
* Total GST
* Grand total
* Payment details

Invoices are generated using the stored bill data.

They are not screenshots or chatbot-formatted text.

---

# 📊 Sales Analysis

The analytics layer retrieves finalized sales from SQLite.

The daily report provides:

```text
Sales summary
Payment-mode breakdown
Top-selling products
Low-stock products
GST summary
```

A PowerPoint report is generated for business analysis.

---

# 🗃️ Data Persistence

SQLite provides durable storage for the store's operational state.

The database contains tables for:

```text
products
customers
owner_preferences
bills
bill_items
```

The database file is:

```text
data/supermarket.db
```

This allows operational data to survive application restarts.

---

# 🔄 Conversation vs Persistent State

The system separates conversational state from persistent business state.

```text
Conversation Context
        │
        └── Temporary conversational information

SQLite
        │
        ├── Products
        ├── Inventory
        ├── Bills
        ├── Customers
        └── Preferences
```

Therefore, restarting/resetting the conversational context does not remove the store's persistent operational data.

---

# 📁 Project Structure

```text
supermarket-ops-agent/
│
├── app/
│   ├── database.py
│   ├── models.py
│   ├── telegram_bot.py
│   ├── config.py
│   └── main.py
│
├── gemini_agent/
│   ├── agent.py
│   └── __init__.py
│
├── tools/
│   ├── inventory.py
│   ├── billing.py
│   ├── customer.py
│   ├── khata.py
│   ├── analytics.py
│   ├── documents.py
│   └── preferences.py
│
├── skills/
│   └── supermarket.md
│
├── data/
│   ├── supermarket.db
│   ├── invoices/
│   └── analysis/
│
├── test_inventory.py
├── test_sell.py
├── test_billing.py
├── test_billing_errors.py
├── test_finalize_bill.py
├── test_gst.py
├── test_gst_finalize.py
├── test_payment.py
├── test_low_stock.py
│
└── README.md
```

---

# ⚙️ Technology Stack

| Component                 | Technology          |
| ------------------------- | ------------------- |
| User Interface            | Telegram            |
| Agent Framework           | Google ADK          |
| AI Model                  | Gemini              |
| Programming Language      | Python              |
| Database                  | SQLite              |
| PDF Generation            | ReportLab           |
| PPTX Generation           | python-pptx         |
| Telegram Integration      | python-telegram-bot |
| Environment Configuration | python-dotenv       |

---

# 🔧 Setup

## 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd supermarket-ops-agent
```

## 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

## 3. Install dependencies

If a `requirements.txt` file is provided with the submission:

```bash
pip install -r requirements.txt
```

The project requires the libraries used by the implementation, including the Google ADK/Gemini integration, Telegram bot framework, environment-variable loader, ReportLab and python-pptx.

## 4. Configure environment variables

Create a `.env` file.

Example:

```env
GOOGLE_API_KEY=your_google_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Do not commit API keys or Telegram bot tokens to GitHub.

## 5. Initialize the database

The application creates the required SQLite tables automatically.

The database is stored at:

```text
data/supermarket.db
```

## 6. Start the Telegram bot

Run:

```bash
python app/telegram_bot.py
```

A successful startup displays:

```text
🛒 Supermarket Ops Agent
Telegram bot starting...
✅ Telegram bot is running...
```

---

# 💬 Example Commands

The owner can use natural language instead of fixed commands.

### Inventory

```text
Check stock of Maggi
```

```text
How many Tata Salt packets do we have?
```

```text
Receive 10 packets of Tata Salt
```

```text
Show low stock products
```

---

### Billing

```text
Create a bill for Ravi
```

```text
Add 2 Maggi to the bill
```

```text
Add 1 Tata Salt
```

```text
Change Maggi quantity to 6
```

```text
Remove Tata Salt
```

```text
Pay using UPI
```

---

### Khata

```text
Create customer Ravi
```

```text
Check Ravi's balance
```

```text
Give this bill on credit
```

```text
Ravi paid 500
```

---

### Documents

```text
Generate invoice for this bill
```

```text
Generate today's sales report
```

---

### Preferences

```text
Remember that my default payment mode is UPI
```

```text
What is my default payment mode?
```

---

# 🧪 Testing

The repository contains focused test scripts for important business operations.

Examples include:

```text
test_inventory.py
test_sell.py
test_billing.py
test_billing_errors.py
test_finalize_bill.py
test_gst.py
test_gst_finalize.py
test_payment.py
test_low_stock.py
```

The tests cover scenarios such as:

* Product creation
* Stock lookup
* Stock receiving
* Low-stock detection
* Overselling
* Multi-item bills
* Bill editing
* Bill finalization
* GST calculation
* Payment validation
* Excess payment/change
* Insufficient payment
* Finalized-bill protection

Run an individual test with:

```bash
python test_inventory.py
```

or:

```bash
python test_billing.py
```

---

# 🎬 Demonstration Flow

The recommended demonstration follows the complete business workflow:

```text
1. Receive stock
       ↓
2. Check inventory
       ↓
3. Create multi-item bill
       ↓
4. Edit bill
       ↓
5. Finalize sale
       ↓
6. Attempt oversell
       ↓
7. Manage customer Khata
       ↓
8. Generate GST invoice PDF
       ↓
9. Generate sales-analysis PPTX
       ↓
10. Save owner preference
       ↓
11. Start a new conversation
       ↓
12. Retrieve remembered preference
```

This demonstrates both the agent capabilities and the persistence/business-rule layer.

---

# 🧠 Design Philosophy

The central design principle is:

> **Reasoning and business rules are kept separate.**

The AI agent is responsible for understanding the owner's natural-language request and composing the required tools.

The business tools are responsible for:

* Reading actual database state
* Validating stock
* Calculating GST
* Validating payments
* Updating inventory
* Updating bills
* Updating customer credit
* Persisting preferences
* Generating business documents

This architecture reduces the risk of hallucinated stock, prices, GST values or financial state.

---

# 🔒 Source of Truth

The Gemini model is **not** treated as the source of truth for business data.

The source of truth is:

```text
SQLite Database
       │
       ├── Product information
       ├── Stock
       ├── Prices
       ├── GST
       ├── Bills
       ├── Bill items
       ├── Customers
       └── Preferences
```

The model retrieves and acts on this information through tools.

---

# 🏆 Why This Is an Agent

This project is intentionally agent-first rather than a traditional keyword/regex intent router.

For a request such as:

> "Make a bill for 2 Maggi and 1 Tata Salt, UPI"

the system must reason about the required sequence of operations:

```text
Understand request
      ↓
Identify products
      ↓
Check database
      ↓
Create bill
      ↓
Add items
      ↓
Retrieve calculated totals
      ↓
Validate payment
      ↓
Finalize
      ↓
Return result
```

The model can select and compose multiple tools depending on the request.

---

# 📌 Project Information

**Project:** Supermarket Ops Agent

**Interface:** Telegram

**Agent Framework:** Google ADK

**Model:** Gemini

**Database:** SQLite

**Language:** Python

**Telegram Bot:** `supermarket_ops_agent`

**Repository:** `<YOUR_PRIVATE_REPOSITORY_URL>`

---

# 👥 Intended User

The system is designed for small Indian supermarkets and kirana stores where the owner may prefer conversational interaction over a complex POS/admin dashboard.

Instead of navigating multiple screens, the owner can simply send requests such as:

> "How much Maggi is left?"

or:

> "Make a bill for Ravi with 2 Maggi and 1 Tata Salt, UPI."

The agent translates these natural-language requests into validated business operations.

---

# 📜 Conclusion

The Supermarket Ops Agent demonstrates how an AI agent can be connected to real business operations while keeping critical business rules outside the language model.

By combining:

* Telegram
* Google ADK
* Gemini
* Python
* SQLite
* Inventory tools
* Billing tools
* Khata management
* GST calculation
* PDF generation
* PPTX analytics
* Persistent preferences

the system provides a practical conversational interface for supermarket operations while maintaining a database-backed source of truth.
