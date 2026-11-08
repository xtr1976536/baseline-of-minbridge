# Financial Metric Knowledge Base

The **Financial Metric Knowledge Base** serves as the foundational data source for constructing the Financial Metric Knowledge Graph (FMKG). Located in the `/knowledge_base` directory, this dataset contains **7,521** financial terms, providing standardized definitions, multilingual aliases (English/Chinese), calculation formulas, and executable Python code for complex metric derivation in json format.

### Field Attributes

```json
{
  "term_en": {
    "name": "[String] Standardized English name",
    "aliases": {
      "chinese": "[List] Chinese synonyms",
      "english": "[List] English synonyms",
      "abbreviations": "[List] Common abbreviations"
    }
  },
  "definition_en": "[String] Semantic definition of the metric",
  "formula_en": "[List] Valid calculation formulas",
  "code": "[List] Executable Python functions corresponding to formulas",
  "related_concepts_en": "[List] Dependencies required for calculation",
  "category_en": "[List] Domain tags"
}

```

### Data Example

```json
{
  "term_en": {
    "name": "Cost of Sales",
    "aliases": {
      "chinese": [
        "销售成本",
        "营业成本",
        "销货成本"
      ],
      "english": [
        "Cost of Goods Sold",
        "Cost of Products Sold",
        "Cost of sales",
        "Cost of Sales"
      ],
      "abbreviations": [
        "COGS",
        "COPS"
      ]
    }
  },
  "definition_en": "Cost of sales refers to the production cost of goods sold or the service cost of services provided, as well as other business costs of sales, including main business costs and other business costs. It is a key item on the income statement used to measure the direct cost expenditures in a company's sales activities.",
  "formula_en": [
    "Cost of Sales = Beginning Inventory Cost + Purchases During the Period - Ending Inventory Cost",
    "Cost of Sales = Net Sales × (1 - Gross Profit Margin)",
    "Cost of Sales = Production Cost of Inventory Goods"
  ],
  "code": [
    "def sales_cost_v1(beginning_inventory_cost, purchase_cost, ending_inventory_cost):\n    return beginning_inventory_cost + purchase_cost - ending_inventory_cost",
    "def sales_cost_v2(net_sales, gross_profit_rate):\n    return net_sales * (1 - gross_profit_rate)",
    "def sales_cost_v3(cost_of_inventory):\n    return cost_of_inventory"
  ],
  "related_concepts_en": [
    {
      "concept": "Beginning Inventory Cost",
      "relation": "Calculation"
    },
    {
      "concept": "Purchases During the Period",
      "relation": "Calculation"
    },
    {
      "concept": "Ending Inventory Cost",
      "relation": "Calculation"
    },
    {
      "concept": "Net Sales",
      "relation": "Calculation"
    },
    {
      "concept": "Gross Profit Margin",
      "relation": "Calculation"
    },
    {
      "concept": "Production Cost of Inventory Goods",
      "relation": "Calculation"
    }
  ],
  "category_en": [
    "Accounting",
    "Corporate",
    "Cost Accounting",
    "Financial Management",
    "Income Statement Analysis",
    "Inventory Management"
  ]
}

```
