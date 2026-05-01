# Databricks notebook source
# MAGIC %md
# MAGIC # F1 Telemetry Data Preview
# MAGIC Automatically displays the 100 most recent records from all tables in the Bronze, Silver, and Gold schemas.

# COMMAND ----------

def display_recent_records(schema_name):
    """Dynamically finds tables in a schema and displays their 100 most recent rows."""
    try:
        tables = spark.sql(f"SHOW TABLES IN f1_catalog.{schema_name}").collect()
        
        if not tables:
            print(f"No tables found in f1_catalog.{schema_name}")
            return
            
        for row in tables:
            table_name = row['tableName']
            full_table_name = f"f1_catalog.{schema_name}.{table_name}"
            print(f"\n=======================================================")
            print(f"Top 100 Recent Records: {full_table_name}")
            print(f"=======================================================\n")
            
            # Safely determine the time column to order by
            cols_df = spark.sql(f"DESCRIBE {full_table_name}").collect()
            cols = [c['col_name'] for c in cols_df if not c['col_name'].startswith('#')]
            
            order_by = ""
            if "processing_time" in cols:
                order_by = "ORDER BY processing_time DESC"
            elif "timestamp" in cols:
                order_by = "ORDER BY timestamp DESC"
            elif "window" in cols:
                order_by = "ORDER BY window.end DESC"
            elif "last_updated" in cols:
                order_by = "ORDER BY last_updated DESC"
                
            query = f"SELECT * FROM {full_table_name} {order_by} LIMIT 50"
            display(spark.sql(query))
            
    except Exception as e:
        print(f"Failed to query schema {schema_name}: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🥉 Bronze Layer

# COMMAND ----------

display_recent_records("bronze")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🥈 Silver Layer

# COMMAND ----------

display_recent_records("silver")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🥇 Gold Layer

# COMMAND ----------

display_recent_records("gold")
