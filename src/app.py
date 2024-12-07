from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from sqlalchemy import create_engine, text
import streamlit as st
import sqlite3
import os
import re

# Load environment variables from the .env file
load_dotenv()

def init_database(db_file: str) -> SQLDatabase:
  db_file = 'sqlite:///src/courses_database.db'
  print('db file:', db_file)
  engine = create_engine(db_file)

  # Using a connection from the engine
  with engine.connect() as connection:
    # Execute your query using the connection (wrapped in text for SQLAlchemy)
    result = connection.execute(text("SELECT sql FROM sqlite_master WHERE type='table';"))
    
    # Fetch all results
    rows = result.fetchall()
    # print('Current working directory:', os.getcwd())
    # print('rows:', rows)  # Output the fetched rows

  # Returning the SQLDatabase object created with the engine
  return SQLDatabase(engine)

def chain_of_thought(user_query, schema):
   print('user_query:', user_query)
  #  print('schema:', schema)
   template = """
      You are a thinker. You are responsible for coming up with a carefully thought out strategy to answer the user's query using the schema given below.
      The label_descriptions in schema documents what the variables in the database consist of
      Based on the user query and schema below, write a carefully thought out strategy on answering the user's question. Take the conversation 
      history into account. Make sure that the response is a string with no formatting
      
      <SCHEMA>{schema}</SCHEMA>
      User query: {user_query}
      
      write out the strategy and nothing else. 
      For example: 
      Question: I am a CMC student. I want to take two technical courses and two fun classes next semester
      Response: Need to identify what courses can be categorized as technical courses and what courses can be categorized
      as fun courses. Using the schema above, it is clear that 'computer science' and 'mathematics' are technical courses. 
      Out of the courses in my database, I can say that 'religious studies' and 'history' are "fun" courses. "fun" courses 
      should also not be hard so that student does not have to spend too much time on the course. Hence need to choose religious 
      studies and history courses that have little prerequisities. Need to sort the religious studies and history courses based
      on the number of prerequisites they have. Student is studying at CMC so it is easier for them to get into a class in CMC compared to
      other campuses. Rank the computer science/math classes and give higher preferences to CMC courses. Also rank the religious studies/history 
      courses and rank CMC courses higher. Student just wants two technical courses and two fun classes so select two
      computer science/math classes and two history/religious studies courses.  

      Question: give me the names of 10 courses given I am a CMC student
      Response: student prefers a diversity of courses. There are 8 course categories so select 1-2 courses from each course category. Student
      is from CMC so rank the courses and give highest preference to CMC courses. Also need to make sure there are no repeated course names/course codes in final results
      because we want to give user a distinct set of courses they can take

      Your turn: 
      Question: {user_query}
      Response: 
    """
   prompt = ChatPromptTemplate.from_template(template)
   llm = ChatOpenAI(model="gpt-4o")
   strategy_chain = (
        RunnablePassthrough.assign(
            schema=lambda _:schema,
            user_query=lambda _:user_query,
        )
        | prompt
        | llm
        | StrOutputParser()
    )
   # Print the strategy before invoking the chain
   strategy_result = strategy_chain.invoke({})
  #  print("Strategy Generated:", strategy_result)
   
   return strategy_result

def get_sql_chain(user_query, schema):
  strategy = chain_of_thought(user_query, schema)
  print('Generated strategy:', strategy)
  template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema, strategy below, write a SQL query that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    strategy: {strategy}
    
    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks. 
    
    For example:
    Question: give me the names of 10 courses given I am a CMC student
    strategy: student prefers a diversity of courses. There are 8 course categories so select 1-2 courses from each course category. Student
    is from CMC so rank the courses and give highest preference to CMC courses. Also need to make sure there are no repeated course names/course codes in final results
    because we want to give user a distinct set of courses they can take
    SQL Query: 
    WITH RankedCourses AS (
    SELECT 
        `Course Name`, 
        `Course Code Short`, 
        campus,
        course,
        ROW_NUMBER() OVER (
            PARTITION BY course 
            ORDER BY 
                CASE campus
                    WHEN 'CM Campus' THEN 1  
                    WHEN 'PZ Campus' THEN 2
                    WHEN 'SC Campus' THEN 3
                    WHEN 'PO Campus' THEN 4
                    WHEN 'HM Campus' THEN 5
                END, 
                `Course Code Short`  
        ) AS rank_in_category
    FROM merged_courses
)
SELECT 
    DISTINCT `Course Name`,
    `Course Code Short`,
    campus,
    course
FROM RankedCourses
WHERE rank_in_category <= 2  
ORDER BY 
    course,  
    CASE campus
        WHEN 'CM Campus' THEN 1
        WHEN 'PZ Campus' THEN 2
        WHEN 'SC Campus' THEN 3
        WHEN 'PO Campus' THEN 4
        WHEN 'HM Campus' THEN 5
    END
LIMIT 16;

    Question: I am a CMC student. I want to take two technical courses and two fun classes next semester
    Strategy: Need to identify what courses can be categorized as technical courses and what courses can be categorized
    as fun courses. Using the schema above, it is clear that 'computer science' and 'mathematics' are technical courses. 
    Out of the courses in my database, I can say that 'religious studies' and 'history' are "fun" courses. "fun" courses 
    should also not be hard so that student does not have to spend too much time on the course. Hence need to choose religious 
    studies and history courses that have little prerequisities. Need to sort the religious studies and history courses based
    on the number of prerequisites they have. Student is studying at CMC so it is easier for them to get into a class in CMC compared to
    other campuses. Rank the computer science/math classes and give higher preferences to CMC courses. Also rank the religious studies/history 
    courses and rank CMC courses higher. Student just wants two technical courses and two fun classes so select two
    computer science/math classes and two history/religious studies courses.
    SQL Query: Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.

    Your turn:
    
    Question: {user_query}
    Strategy: {strategy}
    SQL Query:
    WITH RankedCourses AS (
    -- Selecting and ranking technical courses (computer science and mathematics)
    SELECT 
        `Course Name`, 
        `Course Code Short`, 
        campus,
        course,
        prerequisites,
        ROW_NUMBER() OVER (
            PARTITION BY course 
            ORDER BY 
                CASE campus
                    WHEN 'CM Campus' THEN 1  
                    WHEN 'PZ Campus' THEN 2
                    WHEN 'SC Campus' THEN 3
                    WHEN 'PO Campus' THEN 4
                    WHEN 'HM Campus' THEN 5
                END, 
                `Course Code Short`  
        ) AS rank_in_category
    FROM merged_courses
    WHERE course IN ('computer science', 'mathematics')
    -- Selecting fun courses (religious studies and history)
    UNION ALL
    SELECT 
        `Course Name`, 
        `Course Code Short`, 
        campus,
        course,
        prerequisites,
        ROW_NUMBER() OVER (
            PARTITION BY course 
            ORDER BY 
                CASE campus
                    WHEN 'CM Campus' THEN 1  
                    WHEN 'PZ Campus' THEN 2
                    WHEN 'SC Campus' THEN 3
                    WHEN 'PO Campus' THEN 4
                    WHEN 'HM Campus' THEN 5
                END,
                LENGTH(prerequisites)  
        ) AS rank_in_category
    FROM merged_courses
    WHERE course IN ('religious studies', 'history')
    AND prerequisites IS NULL  
)

SELECT 
    DISTINCT `Course Name`,
    `Course Code Short`,
    campus,
    course
FROM RankedCourses
WHERE (course IN ('computer science', 'mathematics') AND rank_in_category <= 2) 
   OR (course IN ('religious studies', 'history') AND rank_in_category <= 2)  
ORDER BY 
    course,  
    CASE campus
        WHEN 'CM Campus' THEN 1  
        WHEN 'PZ Campus' THEN 2
        WHEN 'SC Campus' THEN 3
        WHEN 'PO Campus' THEN 4
        WHEN 'HM Campus' THEN 5
    END
LIMIT 4;
    """
  prompt = ChatPromptTemplate.from_template(template)
  
  llm = ChatOpenAI(model="gpt-4o")
  
  
  sql_chain = (
        RunnablePassthrough.assign(
            user_query=lambda _:user_query,
            schema=lambda _:schema,
            strategy=lambda _:strategy,
        )
        | prompt
        | llm
        | StrOutputParser()
    )
  # print("SQL query:", sql_chain)
  return sql_chain.invoke({})
  
def get_schema(_):
  # print('_:', _)
  db_file = 'lol'
  db = init_database(db_file)
  schema = {}
  schema['get_table_info'] = db.get_table_info()

  schema['labels_descriptions'] = {
      'Course Code': 'The course code and section identifier.',
      'Instructor_location': 'The professor, time, and location of the class.',
      'Course Name': 'The name of the course.',
      'course': 'The category the course falls into. Use `distinct_courses` to find available categories.',
      'instructor': 'The name of the professor teaching the course.',
      'date_time': 'The days and times the course is offered. Use `day_code` and `time` columns instead.',
      'location': 'The campus, building, and room where the course is taught.',
      'campus': (
          'The campus or college where the course is taught. '
          'Refer to `campuses` for campus names. Unless specified, assume the student is from CMC and '
          'rank courses based on `campus_ranking`.'
      ),
      'Course Code Short': (
          'The shortened course code. The first four letters represent the subject category, '
          'and the last three numbers are unique to each course. Higher numbers indicate harder courses '
          'within the same subject category.'
      ),
      'Course Description': 'A description of the course.',
      'prerequisites': 'Courses that must be completed before enrolling in this course.',
      'Frequency': 'How often the course is generally offered.',
      'day_code': 'The days the course is offered. See `day_codes` for more information.',
      'time': 'The time of day the course is taught. Refer to `distinct_times` for available times.'
  }
  # Add additional metadata to the schema
  schema['distinct_courses'] = {
      'economics', 'computer science', 'mathematics', 
      'religious studies', 'government', 'history', 
      'philosophy', 'psychology'
  }
  schema['campuses'] = {
      'PZ Campus': 'Pitzer campus',
      'CM Campus': 'CMC/Claremont McKenna College campus',
      'SC Campus': 'Scripps campus',
      'PO Campus': 'Pomona campus',
      'HM Campus': 'Harvey Mudd campus'
  }
  schema['day_codes'] = {
      'M': 'Monday',
      'T': 'Tuesday',
      'W': 'Wednesday',
      'R': 'Thursday',
      'F': 'Friday',
      'TR': 'Tuesday and Thursday',
      'MW': 'Monday and Wednesday',
      'WF': 'Wednesday and Friday',
      'MWF': 'Monday, Wednesday, and Friday',
      'To Be Arranged': 'Schedule not determined yet'
  }
  schema['distinct_times'] = {
      '01:15-02:30PM', '11:00AM-12:15PM', '09:35-10:50AM', 
      '08:10-09:25AM', '02:45-04:00PM', '04:15-05:30PM', 
      '02:45-05:30PM', '01:15-04:00PM', '07:00-09:50PM', 
      '07:00-09:45PM', '09:00-09:50AM', '06:00-09:00PM', 
      '00:00-00:00AM', '11:00AM-12:00PM', '11:00-11:50AM', 
      '10:00-10:50AM', '08:00-08:50AM', '06:30-08:00PM', 
      '03:00-05:00PM', '01:15-04:15PM', '03:00-04:00PM'
  }
  
  # Add ranking logic for campuses based on user preference
  schema['campus_ranking'] = {'CM Campus', 'PZ Campus', 'SC Campus', 'PO Campus', 'HM Campus'}

  schema['rules'] = {
      'give higher preference to the courses from the school/campus that user says they stay at',
      'easy/fun courses have fewer prerequisites compared to harder or more technical courses'
  }

  # print('schema:', schema)
  return schema
    
def get_response(user_query: str, db: SQLDatabase, chat_history: list):
  schema = get_schema('lol')
  sql_query = get_sql_chain(user_query, schema)
  # Remove backticks and `sql` tags if present
  sql_query = re.sub(r"```sql|```", "", sql_query).strip()
  print('Cleaned SQL Query:', sql_query)
  
  try:
    db_file = 'lol'
    db = init_database(db_file)
    sql_response = db.run(sql_query)
    print(f"SQL Query: {sql_query}, Response: {sql_response}")
  except Exception as e:
    print(f"Error executing SQL Query: {e}")
    raise
  # sql_response = db.run(sql_query)
  print(f"SQL Query: {sql_query}, Response: {sql_response}")
  
  template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}"""
  
  prompt = ChatPromptTemplate.from_template(template)
  
  # llm = ChatOpenAI(model="gpt-4-0125-preview")
  llm = ChatOpenAI(model="gpt-4o")
  
  chain = (
      RunnablePassthrough.assign(
          schema=lambda _: schema,
          query=lambda _: sql_query,
          response=lambda _: sql_response,
      )
      | prompt
      | llm
      | StrOutputParser()
  )
  
  return chain.invoke({
    "question": user_query,
    "chat_history": chat_history,
  })
    
  
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
      AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
    ]

if "db" not in st.session_state:
    st.session_state.db = None
load_dotenv()

st.set_page_config(page_title="Chat with MySQL", page_icon=":speech_balloon:")

st.title("Chat with SQLite")

with st.sidebar:
    st.subheader("Settings")
    st.write("This is a simple chat application using SQLite. Connect to the database and start chatting.")
    
    st.text_input("Database File", value="courses_database.db", key="DatabaseFile")  # SQLite file path
    if st.button("Connect"):
      with st.spinner("Connecting to database..."):
        db_file = st.session_state["DatabaseFile"]
        db = init_database(db_file)  # Pass the correct db_file
        if db:
            st.session_state.db = db
            st.success("Connected to database!")
        else:
            st.error("Failed to connect to the database.")

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

user_query = st.chat_input("Type a message...")
if user_query is not None and user_query.strip() != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    
    with st.chat_message("Human"):
        st.markdown(user_query)
        
    with st.chat_message("AI"):
        response = get_response(user_query, st.session_state.db, st.session_state.chat_history)
        st.markdown(response)
        
    st.session_state.chat_history.append(AIMessage(content=response))