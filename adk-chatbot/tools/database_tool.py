"""
Database Tool - Executes SQL queries against PostgreSQL
"""
import psycopg2
from typing import Dict, Any
from config.settings import DB_CONFIG


class DatabaseTool:
    """Tool for executing read-only SQL queries against the database"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute a SELECT query and return results
        
        Args:
            sql: The SQL query to execute (must be SELECT only)
        
        Returns:
            Dict with status, results, and any error messages
        """
        # Security check: Only allow SELECT queries
        sql_upper = sql.strip().upper()
        
        if not sql_upper.startswith("SELECT"):
            return {
                "status": "blocked",
                "error": "Only SELECT queries are allowed",
                "results": []
            }
        
        # Block dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", 
                              "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    "status": "blocked",
                    "error": f"Dangerous keyword detected: {keyword}",
                    "results": []
                }
        
        try:
            # Connect and execute
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute(sql)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Format results
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            conn.close()
            
            # Check if results are empty
            if len(results) == 0:
                return {
                    "status": "empty",
                    "results": [],
                    "message": "Query executed successfully but returned no results"
                }
            
            # Return success if we have rows (even if values are NULL/zero)
            return {
                "status": "success",
                "results": results,
                "row_count": len(results)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "results": []
            }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Return information about the v_processed_superstore view
        
        Returns:
            Dict with column names and types
        """
        return {
            "view_name": "v_processed_superstore",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "raw_id", "type": "text"},
                {"name": "ship_mode", "type": "text"},
                {"name": "segment", "type": "text"},
                {"name": "country", "type": "text"},
                {"name": "city", "type": "text"},
                {"name": "state", "type": "text"},
                {"name": "postal_code", "type": "text"},
                {"name": "region", "type": "text"},
                {"name": "category", "type": "text"},
                {"name": "sub_category", "type": "text"},
                {"name": "sales", "type": "numeric"},
                {"name": "quantity", "type": "integer"},
                {"name": "discount", "type": "numeric"},
                {"name": "profit", "type": "numeric"},
                {"name": "profit_margin", "type": "numeric"},
                {"name": "processed_at", "type": "timestamp"}
            ]
        }