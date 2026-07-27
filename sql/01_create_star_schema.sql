/*
    Maven Market analytical star schema
    Target platform: SQL Server

    The script creates empty model tables. Data loading is handled separately.
*/

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'analytics')
    EXEC('CREATE SCHEMA analytics');
GO

DROP TABLE IF EXISTS analytics.FactReturns;
DROP TABLE IF EXISTS analytics.FactSales;
DROP TABLE IF EXISTS analytics.DimStore;
DROP TABLE IF EXISTS analytics.DimProduct;
DROP TABLE IF EXISTS analytics.DimCustomer;
DROP TABLE IF EXISTS analytics.DimDate;
GO

CREATE TABLE analytics.DimDate (
    date_key             INT           NOT NULL PRIMARY KEY,
    [date]               DATE          NOT NULL UNIQUE,
    [year]               SMALLINT      NOT NULL,
    quarter_number       TINYINT       NOT NULL,
    quarter              VARCHAR(2)    NOT NULL,
    month_number         TINYINT       NOT NULL,
    month_name           VARCHAR(9)    NOT NULL,
    month_short_name     VARCHAR(3)    NOT NULL,
    year_month           CHAR(7)       NOT NULL,
    year_month_sort      INT           NOT NULL,
    iso_week_number      TINYINT       NOT NULL,
    day_of_month         TINYINT       NOT NULL,
    day_name             VARCHAR(9)    NOT NULL,
    day_of_week_number   TINYINT       NOT NULL,
    is_weekend           BIT           NOT NULL
);
GO

CREATE TABLE analytics.DimCustomer (
    customer_key                 INT             NOT NULL PRIMARY KEY,
    customer_id                  INT             NOT NULL UNIQUE,
    customer_acct_num            VARCHAR(20)     NOT NULL,
    customer_full_name           NVARCHAR(160)   NOT NULL,
    first_name                   NVARCHAR(80)    NOT NULL,
    last_name                    NVARCHAR(80)    NOT NULL,
    last_name_missing            BIT             NOT NULL,
    customer_city                NVARCHAR(100)   NOT NULL,
    customer_state_province      NVARCHAR(100)   NOT NULL,
    customer_postal_code         VARCHAR(20)     NOT NULL,
    customer_country             NVARCHAR(80)    NOT NULL,
    birthdate                    DATE            NOT NULL,
    birth_year                   SMALLINT        NOT NULL,
    marital_status               VARCHAR(20)     NOT NULL,
    yearly_income                VARCHAR(30)     NOT NULL,
    gender                       VARCHAR(20)     NOT NULL,
    total_children               TINYINT         NOT NULL,
    num_children_at_home         TINYINT         NOT NULL,
    education                    NVARCHAR(80)    NOT NULL,
    acct_open_date               DATE            NOT NULL,
    account_open_year            SMALLINT        NOT NULL,
    member_card                  VARCHAR(20)     NOT NULL,
    occupation                   NVARCHAR(80)    NOT NULL,
    is_homeowner                 BIT             NOT NULL
);
GO

CREATE TABLE analytics.DimProduct (
    product_key              INT             NOT NULL PRIMARY KEY,
    product_id               INT             NOT NULL UNIQUE,
    product_brand            NVARCHAR(100)   NOT NULL,
    product_name             NVARCHAR(200)   NOT NULL,
    product_sku              VARCHAR(20)     NOT NULL,
    product_retail_price     DECIMAL(12,2)   NOT NULL,
    product_cost             DECIMAL(12,2)   NOT NULL,
    unit_gross_profit        DECIMAL(12,2)   NOT NULL,
    unit_margin_pct          DECIMAL(8,2)    NOT NULL,
    unit_markup_pct          DECIMAL(8,2)    NOT NULL,
    product_weight           DECIMAL(10,2)   NOT NULL,
    is_recyclable            BIT             NOT NULL,
    is_low_fat               BIT             NOT NULL
);
GO

CREATE TABLE analytics.DimStore (
    store_key                  INT             NOT NULL PRIMARY KEY,
    store_id                   INT             NOT NULL UNIQUE,
    store_name                 NVARCHAR(100)   NOT NULL,
    store_type                 NVARCHAR(80)    NOT NULL,
    store_city                 NVARCHAR(100)   NOT NULL,
    store_state                NVARCHAR(100)   NOT NULL,
    store_country              NVARCHAR(80)    NOT NULL,
    first_opened_date          DATE            NOT NULL,
    last_remodel_date          DATE            NOT NULL,
    total_sqft                 INT             NOT NULL,
    grocery_sqft               INT             NOT NULL,
    non_grocery_sqft           INT             NOT NULL,
    grocery_share_pct          DECIMAL(6,2)    NOT NULL,
    region_id                  INT             NOT NULL,
    sales_district             NVARCHAR(100)   NOT NULL,
    sales_region               NVARCHAR(100)   NOT NULL,
    is_same_store_comparable   BIT             NOT NULL
);
GO

CREATE TABLE analytics.FactSales (
    sales_line_key          BIGINT          NOT NULL PRIMARY KEY,
    transaction_line_id     VARCHAR(30)     NOT NULL UNIQUE,
    transaction_date_key    INT             NOT NULL,
    stock_date_key          INT             NOT NULL,
    product_key             INT             NOT NULL,
    customer_key            INT             NOT NULL,
    store_key               INT             NOT NULL,
    quantity_sold           SMALLINT        NOT NULL,
    unit_retail_price       DECIMAL(12,2)   NOT NULL,
    unit_product_cost       DECIMAL(12,2)   NOT NULL,
    revenue                 DECIMAL(18,2)   NOT NULL,
    product_cost_amount     DECIMAL(18,2)   NOT NULL,
    gross_product_profit    DECIMAL(18,2)   NOT NULL,
    source_year             SMALLINT        NOT NULL,
    source_row_number       INT             NOT NULL,
    duplicate_candidate     BIT             NOT NULL,
    CONSTRAINT FK_FactSales_TransactionDate FOREIGN KEY (transaction_date_key)
        REFERENCES analytics.DimDate(date_key),
    CONSTRAINT FK_FactSales_StockDate FOREIGN KEY (stock_date_key)
        REFERENCES analytics.DimDate(date_key),
    CONSTRAINT FK_FactSales_Product FOREIGN KEY (product_key)
        REFERENCES analytics.DimProduct(product_key),
    CONSTRAINT FK_FactSales_Customer FOREIGN KEY (customer_key)
        REFERENCES analytics.DimCustomer(customer_key),
    CONSTRAINT FK_FactSales_Store FOREIGN KEY (store_key)
        REFERENCES analytics.DimStore(store_key)
);
GO

CREATE TABLE analytics.FactReturns (
    return_line_key        BIGINT          NOT NULL PRIMARY KEY,
    return_line_id         VARCHAR(30)     NOT NULL UNIQUE,
    return_date_key        INT             NOT NULL,
    product_key            INT             NOT NULL,
    store_key              INT             NOT NULL,
    return_quantity        SMALLINT        NOT NULL,
    source_row_number      INT             NOT NULL,
    duplicate_candidate   BIT             NOT NULL,
    CONSTRAINT FK_FactReturns_Date FOREIGN KEY (return_date_key)
        REFERENCES analytics.DimDate(date_key),
    CONSTRAINT FK_FactReturns_Product FOREIGN KEY (product_key)
        REFERENCES analytics.DimProduct(product_key),
    CONSTRAINT FK_FactReturns_Store FOREIGN KEY (store_key)
        REFERENCES analytics.DimStore(store_key)
);
GO

CREATE INDEX IX_FactSales_TransactionDate ON analytics.FactSales(transaction_date_key);
CREATE INDEX IX_FactSales_Product ON analytics.FactSales(product_key);
CREATE INDEX IX_FactSales_Customer ON analytics.FactSales(customer_key);
CREATE INDEX IX_FactSales_Store ON analytics.FactSales(store_key);
CREATE INDEX IX_FactReturns_Date ON analytics.FactReturns(return_date_key);
CREATE INDEX IX_FactReturns_Product ON analytics.FactReturns(product_key);
CREATE INDEX IX_FactReturns_Store ON analytics.FactReturns(store_key);
GO
