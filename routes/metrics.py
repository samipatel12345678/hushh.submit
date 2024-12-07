from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from config.supabase import supabase  # Importing the Supabase client
from config.supabase import supabase

router = APIRouter()
app = FastAPI()

class MetricsRequest(BaseModel):
    start_date: datetime.date
    end_date: datetime.date
scheduler = BackgroundScheduler()

class MetricsResponse(BaseModel):
    insight_date: str  # Change to string to handle serialization
    average_ctr: float
    top_queries: list[str]
    low_performance_queries: list[str]
@router.post("/update-insights", response_model=MetricsResponse)
async def update_search_insights(request: MetricsRequest):
def update_search_insights_cron():
    try:
        # Log the request dates to verify correctness
        print("Request Start Date:", request.start_date)
        print("Request End Date:", request.end_date)
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=1)
        end_date = today - datetime.timedelta(days=1)

        # Step 1: Fetch raw data for the date range
        response = supabase.from_("search_click").select("*") \
            .gte("search_date", request.start_date) \
            .lte("search_date", request.end_date) \
            .gte("search_date", start_date) \
            .lte("search_date", end_date) \
            .execute()

        # Log the full response to check for errors or missing data
        print("Full response:", response)
        # Extract data
        raw_data = response.data
        print("This is raw_data:", raw_data)

        # Step 2: Perform calculations if raw_data exists
        if not raw_data:
            print("No data returned for the given date range.")
            return MetricsResponse(
                insight_date=datetime.date.today().isoformat(),  # Convert date to string
                average_ctr=0.0,
                top_queries=[],
                low_performance_queries=[]
            )
        # Calculate daily average CTR
            return
        daily_ctr = {}
        for record in raw_data:
            date = record["search_date"]
@@ -54,9 +31,7 @@ async def update_search_insights(request: MetricsRequest):

        average_ctr_per_day = {date: sum(ctr_list) / len(ctr_list) for date, ctr_list in daily_ctr.items()}
        overall_average_ctr = sum(average_ctr_per_day.values()) / len(average_ctr_per_day)
        print("This is daily ctr: ", daily_ctr)

        # Identify top 5 queries by CTR
        query_ctr = {}
        for record in raw_data:
            query = record["search_query"]
@@ -65,58 +40,42 @@ async def update_search_insights(request: MetricsRequest):

        average_query_ctr = {query: sum(ctr_list) / len(ctr_list) for query, ctr_list in query_ctr.items()}
        top_queries = sorted(average_query_ctr, key=average_query_ctr.get, reverse=True)[:5]
        print("This is query ctr: ", query_ctr)

        low_performance_queries = []
        # Create a dictionary to store impressions and clicks for each query
        query_metrics = {}
        # Step through raw_data to accumulate impressions and clicks for each query
        for record in raw_data:
            query = record["search_query"]
            ctr = record["clicks"]
            impression = record["impressions"]  # Assuming 'impression' is the field name for impressions
            
            # Initialize or accumulate impressions and clicks for the query
            impression = record["impressions"]
            if query not in query_metrics:
                query_metrics[query] = {"impressions": 0, "total_clicks": 0}
            
            # Accumulate impressions and clicks
            query_metrics[query]["impressions"] += impression  # Use the actual impression value
            query_metrics[query]["impressions"] += impression
            query_metrics[query]["total_clicks"] += ctr

        # Now, loop through the query_metrics to find low performance queries
        for query, metrics in query_metrics.items():
            impressions = metrics["impressions"]
            total_clicks = metrics["total_clicks"]
            
            # Log the query's impressions and total clicks
            print(f"Query: {query}, Impressions: {impressions}, Total Clicks: {total_clicks}")
            # Low performance query criteria: high impressions and low total clicks
            if impressions > 500 and total_clicks <= 200:
                low_performance_queries.append(query)

        print("Low performance queries:", low_performance_queries)  # Log the final result
        # Step 3: Insert metrics into `search_insights`
        insight_date = datetime.date.today().isoformat()  # Convert date to string for database insertion
        insight_date = today.isoformat()
        insights_data = [{
            "insight_date": insight_date,
            "average_ctr": overall_average_ctr,
            "top_queries": top_queries,
            "low_performance_queries": low_performance_queries,
        }]
        insert_response = supabase.from_("search_insights").insert(insights_data).execute()
        # Return response with date as string
        return MetricsResponse(
            insight_date=insight_date,  # Return as string
            average_ctr=overall_average_ctr,
            top_queries=top_queries,
            low_performance_queries=low_performance_queries
        )
        supabase.from_("search_insights").insert(insights_data).execute()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating search insights: {str(e)}")
        print(f"Error updating search insights: {str(e)}")
def start_scheduler():
    scheduler.add_job(update_search_insights_cron, "cron", hour=9, minute=0)
    scheduler.start()
def shutdown_scheduler():
    scheduler.shutdown()
app.add_event_handler("startup", start_scheduler)
app.add_event_handler("shutdown", shutdown_scheduler)
‎routes/processing.py
+1
-8
Original file line number	Diff line number	Diff line change
@@ -6,11 +6,9 @@

router = APIRouter()

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDYTAnPjkk3o-1s9kL1P4Dv1qkgSs25Fsg"
genai.configure(api_key=GEMINI_API_KEY)

# Define Pydantic models
class ProcessingRequest(BaseModel):
    raw_text: str

@@ -20,7 +18,6 @@ class ProcessingResponse(BaseModel):
    summary: str
    keywords: list[str]

# POST /process - Process raw text using the Gemini API
@router.post("/process", response_model=ProcessingResponse)
def process_text(request: ProcessingRequest):
    prompt = (
@@ -31,18 +28,14 @@ def process_text(request: ProcessingRequest):
    )

    try:
        # Use the `google.generativeai` package to generate content
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print(response.text)  # This will output the generated JSON as a string
        print(response.text)  

        # Remove the Markdown formatting from the response text
        cleaned_response = re.sub(r"^```json|```$", "", response.text).strip()

        # Parse the cleaned response as JSON
        structured_response = json.loads(cleaned_response)

        # Validate the parsed response with Pydantic
        processed_data = ProcessingResponse(**structured_response)
        return processed_data
