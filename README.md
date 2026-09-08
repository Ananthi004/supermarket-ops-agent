# 🛒 Supermarket Ops Agent

An AI-powered supermarket management agent designed for small Indian supermarkets and kirana stores.

The agent provides a **Telegram-based conversational interface** through which store owners can manage inventory, billing, customer credit (Khata), sales analytics, GST calculations, and business documents using natural language.

---

## 📌 Project Overview

**Supermarket Ops Agent** is an agent-first AI application built using **Google Agent Development Kit (ADK)** and **Gemini**.

Instead of requiring the store owner to navigate multiple menus or remember commands, the user can simply communicate with the agent in natural language.

### Example

```text
User:
Add 20 packets of Maggi to stock

Agent:
20 packets of Maggi have been added to inventory.
```

```text
User:
Create a bill for Ravi with 2 Maggi and 1 Tata Salt

Agent:
Draft bill created for Ravi with the selected items.
```

The agent observes the current business state, reasons about the request, performs the required operation using business tools, and continues the interaction.

---

## ✨ Key Features

### 📦 Inventory Management

* Add new products
* Check product stock
* Receive stock
* Sell/decrement stock
* Check low-stock products
* Set product price/MRP
* Store cost price
* Store GST rate
* Configure reorder level
* Prevent selling more stock than available

---

### 🧾 Billing

* Create draft bills
* Add products to a bill
* Update quantities
* Remove bill items
* View bill details
* Calculate subtotal
* Calculate GST
* Calculate CGST and SGST
* Support different payment modes
* Finalize sales
* Generate GST invoices

Bill items preserve the product information used at the time of billing.

---

### 📒 Khata / Customer Credit

The agent supports customer credit management.

Features include:

* Create customers
* Record credit purchases
* Check outstanding balance
* Record customer payments
* Finalize credit bills
* Maintain customer balances

Example:

```text
User:
How much does Ravi owe?

Agent:
Ravi's outstanding balance is ₹850.
```

---

### 📊 Sales Analytics

The system can provide daily sales information including:

* Total sales
* Total tax
* Payment-mode breakdown
* Top-selling products
* Low-stock products
* Daily sales summary

---

### 📄 Document Generation

The agent can generate real business documents.

#### GST Invoice

A finalized bill can be converted into a PDF GST invoice.

```text
data/invoices/
```

#### Sales Analysis

Daily sales information can be converted into a PowerPoint report.

```text
data/analysis/
```

---

### 🧠 Persistent Preferences

The system stores important store preferences in SQLite.

Examples:

```text
User:
Set UPI as my default payment mode.

Agent:
Your default payment mode has been saved as UPI.
```

The preference can be retrieved later instead of relying only on the current conversation.

---

## 🤖 Agent Architecture

The project follows an agent-first architecture.

```text
                 ┌─────────────────────┐
                 │      Telegram       │
                 │      Interface      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Google ADK Agent  │
                 │       + Gemini      │
                 └──────────┬──────────┘
                            │
                     Reason / Decide
                            │
                            ▼
                 ┌─────────────────────┐
                 │       Tools         │
                 ├─────────────────────┤
                 │ Inventory           │
                 │ Billing             │
                 │ Customer / Khata    │
                 │ Analytics           │
                 │ Documents           │
                 │ Preferences         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       SQLite        │
                 │      Database       │
                 └─────────────────────┘
```

---

## 🔄 Agent Control Loop

The agent follows an iterative control loop:

```text
Observe
   ↓
Reason
   ↓
Act
   ↓
Observe
   ↓
Continue
```

For example:

```text
User:
Sell 5 Maggi packets.

        ↓

Agent checks inventory

        ↓

Agent verifies available stock

        ↓

Agent performs the sale

        ↓

Database stock is updated

        ↓

Agent reports the result
```

The language model does not directly modify the database. Business operations are performed through controlled application tools.

---

## 🛡️ Business Rules & Guardrails

The system contains business-layer validation to avoid incorrect operations.

### Stock Protection

The agent checks available stock before selling.

```text
Available stock: 3

User requests: Sell 5

Result:
Sale rejected because only 3 items are available.
```

### GST Protection

GST values are calculated using the GST information stored for the product rather than allowing the model to invent tax values.

### Draft Bill Protection

Stock is intended to change only when the bill is finalized.

This allows users to:

* Add items
* Change quantities
* Remove items
* Review the bill

before completing the sale.

### Database Validation

Important operations are handled in the application/business layer to maintain consistent inventory, billing, and customer data.

---

## 🗃️ Database

The project uses **SQLite** for persistent business data.

Main entities include:

```text
Products
Customers
Owner Preferences
Bills
Bill Items
```

Database file:

```text
data/supermarket.db
```

SQLite was selected because it is lightweight and suitable for a small supermarket application.

---

## 📁 Project Structure

```text
supermarket/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── telegram_bot.py
│
├── gemini_agent/
│   ├── __init__.py
│   └── agent.py
│
├── tools/
│   ├── __init__.py
│   ├── analytics.py
│   ├── billing.py
│   ├── customer.py
│   ├── documents.py
│   ├── inventory.py
│   ├── khata.py
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
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 🛠️ Technologies Used

| Technology    | Purpose                        |
| ------------- | ------------------------------ |
| Python        | Main programming language      |
| Google ADK    | Agent development framework    |
| Gemini        | Large language model           |
| Telegram      | User interface                 |
| SQLite        | Persistent database            |
| ReportLab     | GST invoice PDF generation     |
| python-pptx   | Sales analysis PPTX generation |
| python-dotenv | Environment configuration      |

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd supermarket
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure environment variables

Create a `.env` file in the project root.

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

**Do not upload the `.env` file to GitHub.**

---

## ▶️ Running the Application

Start the Telegram bot using:

```bash
python app/telegram_bot.py
```

After starting the application, open your Telegram bot and send:

```text
/start
```

You can then interact with the supermarket agent using natural language.

---

## 💬 Example Commands

### Inventory

```text
Add Maggi with price 15 and stock 50
```

```text
How much Maggi is available?
```

```text
Show me low stock products
```

```text
Receive 20 Tata Salt
```

---

### Billing

```text
Create a bill
```

```text
Add 2 Maggi to bill 12
```

```text
Change Maggi quantity to 3
```

```text
Remove Tata Salt from bill 12
```

```text
Finalize bill 12
```

---

### Khata

```text
Create customer Ravi
```

```text
How much does Ravi owe?
```

```text
Record ₹500 payment from Ravi
```

---

### Analytics

```text
Show today's sales
```

```text
What are my top selling products today?
```

```text
Show payment mode breakdown
```

---

### Documents

```text
Generate GST invoice for bill 12
```

```text
Generate today's sales analysis
```

---

### Preferences

```text
Set UPI as my default payment mode
```

```text
What is my default payment mode?
```

---

## 🧪 Testing

The project includes test scripts for major business operations.

Examples:

```bash
python test_inventory.py
python test_sell.py
python test_billing.py
python test_billing_errors.py
python test_finalize_bill.py
python test_gst.py
python test_gst_finalize.py
python test_payment.py
python test_low_stock.py
```

These tests cover inventory, billing, GST, payments, stock validation, and other business rules.

---

## 🔐 Security

Sensitive configuration values should be stored in `.env`.

The following files should not be committed:

```text
.env
venv/
__pycache__/
.adk/
*.log
```

The `.gitignore` file is included to prevent accidental commits of these files.

---

## 🎯 Demo Workflow

A complete demonstration of the system can follow this sequence:

```text
1. Receive stock
       ↓
2. Add products
       ↓
3. Check inventory
       ↓
4. Create multi-item bill
       ↓
5. Edit bill
       ↓
6. Attempt oversell
       ↓
7. System rejects invalid sale
       ↓
8. Finalize bill
       ↓
9. Manage Khata
       ↓
10. View daily sales
       ↓
11. Generate GST PDF
       ↓
12. Generate sales PPTX
       ↓
13. Save a store preference
       ↓
14. Start a new chat
       ↓
15. Verify remembered preference
```

---

## 🌟 Design Philosophy

The project follows three important principles:

### 1. Natural Language First

Users should be able to express business tasks naturally rather than learning rigid commands.

### 2. Grounded Business Operations

The AI model is not treated as the source of truth for inventory, prices, GST, bills, or customer balances.

Actual business state is retrieved from SQLite through controlled tools.

### 3. AI + Deterministic Business Logic

The AI handles:

```text
Understanding → Reasoning → Tool Selection
```

The application handles:

```text
Validation → Database Operations → Business Rules
```

This separation makes the system more reliable for real-world supermarket operations.

---

## 🚀 Future Enhancements

Potential future improvements include:

* Voice-based supermarket operations
* Barcode scanning
* Multi-store support
* Supplier management
* Purchase order management
* Expiry-date tracking
* Advanced sales forecasting
* WhatsApp integration
* Cloud database synchronization
* Multi-user staff accounts
* Role-based access control
* Automatic reorder recommendations
* More advanced business dashboards

---

## 📌 Project Status

**Status:** Working Prototype / Academic Project

The current implementation demonstrates an AI agent capable of performing supermarket inventory, billing, customer credit, analytics, document generation, and preference-management tasks through a Telegram conversational interface.

---

## 👩‍💻 Author

**Ananthi R**

Final Year Computer Science and Engineering Student

---

## 📄 License

This project is developed for academic and demonstration purposes.
