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
    result = connection.execute(text("SELECT sql FROM sqlite_master WHERE type='table';"))
    rows = result.fetchall()
    # for row in rows:
      # print('rows:', row)
    # print('Current working directory:', os.getcwd())
    # print('rows:', rows)  # Output the fetched rows

  # Returning the SQLDatabase object created with the engine
  return SQLDatabase(engine)

def chain_of_thought(user_query, schema, chat_history):
   print('user_query:', user_query)
  #  print('schema:', schema)
   template = """
      You are a thinker. You are responsible for coming up with a carefully thought out strategy to answer the user's query using the schema given below.
      The label_descriptions in schema documents what the variables in the database consist of
      Based on the user query, schema and chat history below, write a carefully thought out strategy on answering the user's question. Take the conversation 
      history into account. For column names, strictly adhere to schema. Make sure that the response is a string with no formatting
      
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
      computer science/math classes and two history/religious studies courses. Also have a look at schema to make sure all bases are covered

      Question: give me the names of 10 courses given I am a CMC student
      Response: student prefers a diversity of courses. There are 8 course categories so select 1-2 courses from each course category. Student
      is from CMC so rank the courses and give highest preference to CMC courses. Also need to make sure there are no repeated course names/course codes in final results
      because we want to give user a distinct set of courses they can take. Also have a look at schema to make sure all bases are covered

      Question: I am applying to the Lowe Institute. Here is the job description:
      Data Journalists (DJs) will work in a team with Professor Cameron Shelton, Lowe Institute Director, and Dr. Minjae Yun, Lowe Assistant Director, to develop content for the Institute’s Lowe Down blog and social media accounts. 
      Content will be defined based on the DJs research interests as well as the Lowe Institute’s focus on economics, politics, healthcare, education, transportation, and environmental studies pertinent to the Inland Empire and California.
      DJs will need to be entrepreneurial in helping to generate ideas, pursue and analyze data, and write content. A weekly meeting with the entire group is required. Meeting deadlines is critical to success. DJs are expected to produce at least one publishable article a semester, 
      and they are encouraged to work individually and in teams.
      This role is a good fit for those interested in public intellectualism, journalism, and the intersection of academia and the public. This is a young and expanding program and DJs will be expected to provide energy and ideas in helping expand the program. Successful participants will show 
      initiative while taking editorial direction in pursuit of data analysis and writing.
      Qualifications:
      Basic data visualization and data analysis skills (e.g., graph creation and design, pivot tables, functions, basic transformations, regression)
      Strong at reading, interpreting, and analyzing graphs/data tables; able to make economic inferences based on data
      Completion of Econ 50 is required; completion of Econ 120 is extremely useful
      Strong writing skills
      Ability to adhere to established article posting deadlines
      We expect to hire 8 to 12 Data Journalists, which may include returning "EJs" from the previous year.
      Apply on Handshake, job posting job 9208561
      What courses can I take to make me a good applicant for this job?
      Response: This looks like a job that combines investigative journalism and data analysis. First step would looking for hints in the job description. The job description says that the user should take ECON050 and ECON120.
      These are course codes so these courses should be recommended
      Second step would be collecting all the keywords that can be useful to filter within both course description and course name
      This is a comprehensive list of keywords for this job description: "economics", "politics", "healthcare", "education", "transportation", "environment", "enterpreneurial", "data analysis", 
      "writing", "journalism", "data visualization", "regression".  Then do a full text search within course descriptions to identify courses with all the keywords and sort the courses based 
      on how many keywords they have from the list we created. Based on the rules in the schema, I assume student is from CMC so when recommending courses I would give first preference to CMC courses. 
      To not overload students with too much info, recommend upto 10 courses maximum. Also have a look at schema to make sure all bases are covered

      Question: I have taken the following courses: Principles of Economic Analysis, Intermediate Microeconomics, Economics Statistics, Computing for the Web,
      Literature GE, History GE and Psychology GE. I am an Economics major so I want to take two Economics courses next semester, one philosophy GE and one
      government GE. Can you recommend me a course scheule? I also prefer afternoon classes
      Response: First identify that the courses are course names not course code. User wants to take two Economics courses next semester. Filter economics courses by 
      looking at prerequisites and choosing two economics courses that have prerequisites that student has already met or no prerequisites at all. Make sure that courses suggested are not courses that user has already taken. Also give first preference
      to courses that satisfy Economics major requirements from schema
      To identify courses that are taken, take keywords from courses that user has mentioned and make sure that final list of course names do not have these keywords. In this scenario keywords would be "Principles of Economic", 
      "Microeconomics", "Statistics". The schema provides the criteria in order to qualify the philosophy course for philosophy GE or government course for government GE. According to schema, any philosophy course with course code below 
      59 satisifies philosophy GE. Also Introduction American Politics course satisfies government GE. User might want multiple timetables that they can choose from so provide at least 4 different sets of 2 economics courses, 1 philosophy GE and 1 government GE.
      Student also prefers afternoon classes so give higher preference to time in the afternoon. Also have a look at schema to make sure all bases are covered

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

def get_sql_chain(user_query, schema, chat_history):

  strategy = chain_of_thought(user_query, schema, chat_history)
  print('Generated strategy:', strategy)
  template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema, strategy below, write a SQL query that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    strategy: {strategy}
    
    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks. For column names, strictly adhere to schema.
    
    For example:
    Question: give me the names of 10 courses given I am a CMC student
    strategy: student prefers a diversity of courses. There are 8 course categories so select 1-2 courses from each course category. Student
    is from CMC so rank the courses and give highest preference to CMC courses. Also need to make sure there are no repeated course names/course codes in final results
    because we want to give user a distinct set of courses they can take. Also have a look at schema to make sure all bases are covered
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
    computer science/math classes and two history/religious studies courses. Also have a look at schema to make sure all bases are covered
    SQL Query: Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
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
    Question: I have taken the following courses: Principles of Economic Analysis, Intermediate Microeconomics, Economics Statistics, Computing for the Web,
    Literature GE, History GE and Psychology GE. I am an Economics major so I want to take two Economics courses next semester, one philosophy GE and one
    government GE. Can you recommend me a course scheule? I also prefer afternoon classes
    Strategy: First identify that the courses are course names not course code. User wants to take two Economics courses next semester. Filter economics courses by 
    looking at prerequisites and choosing two economics courses that have prerequisites that student has already met or no prerequisites at all. Make sure that courses suggested are not courses that user has already taken.
    Also give first preference to courses that satisfy Economics major requirements from schema
    To identify courses that are taken, take keywords from courses that user has mentioned and make sure that final list of course names do not have these keywords. In this scenario keywords would be "Principles of Economic", 
    "Microeconomics", "Statistics". Sort the courses in some random order not strictly increasing or decreasing
    The schema provides the criteria in order to qualify the philosophy course for philosophy GE or government course for government GE. According to schema, any philosophy course with course code below 
    59 satisifies philosophy GE. Also Introduction American Politics course satisfies government GE. User might want multiple timetables that they can choose from so provide at least 4 different sets of 2 economics courses, 1 philosophy GE and 1 government GE.
    Student also prefers afternoon classes so give higher preference to time in the afternoon. Also have a look at schema to make sure all bases are covered
    SQL Query:
    WITH taken_courses AS (
    SELECT DISTINCT "Course Name"
    FROM merged_courses
    WHERE "Course Name" LIKE '%Principles of Economic%'
       OR "Course Name" LIKE '%Microeconomics%'
       OR "Course Name" LIKE '%Statistics%'
       OR "Course Name" LIKE '%Computing for the Web%'
       OR "Course Name" LIKE '%seminar%'
       OR "Course Name" LIKE '%research%'
       OR "Course Name" LIKE '%Special Topics%'
),
economics_major_courses AS (
    SELECT *
    FROM merged_courses
    WHERE course = 'economics'
      AND (
          "Course Code Short" IN ('ECON050', 'ECON101', 'ECON102', 'ECON125')
          OR CAST(SUBSTR("Course Code Short", 5, 3) AS INTEGER) > 125
      )
      AND "Course Name" NOT IN (SELECT "Course Name" FROM taken_courses) -- Exclude taken courses
      AND time LIKE '%PM%' -- Afternoon preference
    ORDER BY
        
        CASE campus
            WHEN 'CM Campus' THEN 1
            WHEN 'PZ Campus' THEN 2
            WHEN 'SC Campus' THEN 3
            WHEN 'PO Campus' THEN 4
            WHEN 'HM Campus' THEN 5
            ELSE 6
        END,
        "Course Code Short"
    LIMIT 8 -- Get a maximum of 8 economics courses
),
philosophy_ge AS (
    SELECT *
    FROM merged_courses
    WHERE course = 'philosophy'
      AND CAST(SUBSTR("Course Code Short", 5, 3) AS INTEGER) < 59 -- Philosophy GE requirement
      AND time LIKE '%PM%' -- Afternoon preference
    LIMIT 4
),
government_ge AS (
    SELECT *
    FROM merged_courses
    WHERE "Course Name" = 'Introduction American Politics' -- Government GE requirement
      AND time LIKE '%PM%' -- Afternoon preference
    LIMIT 4
)
SELECT *
FROM economics_major_courses -- Selected economics courses
UNION ALL
SELECT *
FROM philosophy_ge -- Selected philosophy GE course
UNION ALL
SELECT *
FROM government_ge;

    Question: I am applying to the Lowe Institute. Here is the job description:
      Data Journalists (DJs) will work in a team with Professor Cameron Shelton, Lowe Institute Director, and Dr. Minjae Yun, Lowe Assistant Director, to develop content for the Institute’s Lowe Down blog and social media accounts. 
      Content will be defined based on the DJs research interests as well as the Lowe Institute’s focus on economics, politics, healthcare, education, transportation, and environmental studies pertinent to the Inland Empire and California.
      DJs will need to be entrepreneurial in helping to generate ideas, pursue and analyze data, and write content. A weekly meeting with the entire group is required. Meeting deadlines is critical to success. DJs are expected to produce at least one publishable article a semester, 
      and they are encouraged to work individually and in teams.
      This role is a good fit for those interested in public intellectualism, journalism, and the intersection of academia and the public. This is a young and expanding program and DJs will be expected to provide energy and ideas in helping expand the program. Successful participants will show 
      initiative while taking editorial direction in pursuit of data analysis and writing.
      Qualifications:
      Basic data visualization and data analysis skills (e.g., graph creation and design, pivot tables, functions, basic transformations, regression)
      Strong at reading, interpreting, and analyzing graphs/data tables; able to make economic inferences based on data
      Completion of Econ 50 is required; completion of Econ 120 is extremely useful
      Strong writing skills
      Ability to adhere to established article posting deadlines
      We expect to hire 8 to 12 Data Journalists, which may include returning "EJs" from the previous year.
      Apply on Handshake, job posting job 9208561
      What courses can I take to make me a good applicant for this job?
      Response: This looks like a job that combines investigative journalism and data analysis. First step would looking for hints in the job description. The job description says that the user should take ECON050 and ECON120.
      These are course codes so these courses should be recommended
      Second step would be collecting all the keywords that can be useful to filter within both course description and course name
      This is a comprehensive list of keywords for this job description: "economics", "politics", "healthcare", "education", "transportation", "environment", "enterpreneurial", "data analysis", 
      "writing", "journalism", "data visualization", "regression".  Then do a full text search within course descriptions to identify courses with all the keywords and sort the courses based 
      on how many keywords they have from the list we created. Based on the rules in the schema, I assume student is from CMC so when recommending courses I would give first preference to CMC courses. 
      To not overload students with too much info, recommend upto 10 courses maximum. Also have a look at schema to make sure all bases are covered
      SQL Query:
      WITH keyword_matches AS (
    SELECT 
        *,
        -- Count how many keywords are present in the course description or name
        ( 
            (LOWER("Course Description") LIKE '%economics%') + 
            (LOWER("Course Description") LIKE '%politics%') +
            (LOWER("Course Description") LIKE '%healthcare%') +
            (LOWER("Course Description") LIKE '%education%') +
            (LOWER("Course Description") LIKE '%transportation%') +
            (LOWER("Course Description") LIKE '%environment%') +
            (LOWER("Course Description") LIKE '%entrepreneurial%') +
            (LOWER("Course Description") LIKE '%data analysis%') +
            (LOWER("Course Description") LIKE '%writing%') +
            (LOWER("Course Description") LIKE '%journalism%') +
            (LOWER("Course Description") LIKE '%data visualization%') +
            (LOWER("Course Description") LIKE '%regression%') +
            (LOWER("Course Name") LIKE '%economics%') +
            (LOWER("Course Name") LIKE '%politics%') +
            (LOWER("Course Name") LIKE '%healthcare%') +
            (LOWER("Course Name") LIKE '%education%') +
            (LOWER("Course Name") LIKE '%transportation%') +
            (LOWER("Course Name") LIKE '%environment%') +
            (LOWER("Course Name") LIKE '%entrepreneurial%') +
            (LOWER("Course Name") LIKE '%data analysis%') +
            (LOWER("Course Name") LIKE '%writing%') +
            (LOWER("Course Name") LIKE '%journalism%') +
            (LOWER("Course Name") LIKE '%data visualization%') +
            (LOWER("Course Name") LIKE '%regression%')
        ) AS keyword_score
    FROM 
        merged_courses
    WHERE 
        "Course Code Short" IN ('ECON050', 'ECON120') -- Include these as high-priority courses
        OR (
            LOWER("Course Description") LIKE '%economics%'
            OR LOWER("Course Description") LIKE '%politics%'
            OR LOWER("Course Description") LIKE '%healthcare%'
            OR LOWER("Course Description") LIKE '%education%'
            OR LOWER("Course Description") LIKE '%transportation%'
            OR LOWER("Course Description") LIKE '%environment%'
            OR LOWER("Course Description") LIKE '%entrepreneurial%'
            OR LOWER("Course Description") LIKE '%data analysis%'
            OR LOWER("Course Description") LIKE '%writing%'
            OR LOWER("Course Description") LIKE '%journalism%'
            OR LOWER("Course Description") LIKE '%data visualization%'
            OR LOWER("Course Description") LIKE '%regression%'
            OR LOWER("Course Name") LIKE '%economics%'
            OR LOWER("Course Name") LIKE '%politics%'
            OR LOWER("Course Name") LIKE '%healthcare%'
            OR LOWER("Course Name") LIKE '%education%'
            OR LOWER("Course Name") LIKE '%transportation%'
            OR LOWER("Course Name") LIKE '%environment%'
            OR LOWER("Course Name") LIKE '%entrepreneurial%'
            OR LOWER("Course Name") LIKE '%data analysis%'
            OR LOWER("Course Name") LIKE '%writing%'
            OR LOWER("Course Name") LIKE '%journalism%'
            OR LOWER("Course Name") LIKE '%data visualization%'
            OR LOWER("Course Name") LIKE '%regression%'
        )
),
ranked_courses AS (
    SELECT 
        *,
        -- Give priority to CMC courses and sort by keyword_score
        CASE
            WHEN LOWER(campus) = 'cm campus' THEN 1
            ELSE 2
        END AS campus_rank
    FROM 
        keyword_matches
)
SELECT 
    "Course Code", 
    "Course Name", 
    "instructor", 
    "date_time", 
    "location", 
    "campus", 
    "Course Code Short", 
    "Course Description", 
    "prerequisites"
FROM 
    ranked_courses
ORDER BY 
    campus_rank, 
    keyword_score DESC
LIMIT 10;

    Your turn:
    
    Question: {user_query}
    Strategy: {strategy}

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
      'easy/fun courses have fewer prerequisites compared to harder or more technical courses',
      'make sure course names recommended are different. A course should not be recommended more than once in the same response',
      'Math or CS GE can be satisified by any computer science or math course in any of the campuses',
      'literature GE can be satified by any literature courses offered at CMC',
      'philosophy GE can be satisifed by any philosophy course with course code less than 59',
      'religious studies GE can be satisifed by any course with course code below 180',
      'economics GE can be satisfied by Principles of Economic Analysis',
      'government GE can be staisifed by Introduction American Politics',
      'history GE can be satisfied by any CMC history course',
      'psychology GE can be satisifed by pscychology course numbered under 100',
      'in SQL query ensure "Course Name", "course", "instructor", "date_time", "location", "campus", "Course Code Short", "Course Description", "day_code", "time" "prerequisites" are returned',
      'provde user with aternative timetables not just one strict response. For example if user asks for two econ courses and 2 psychology courses, provide 4 timetables each with 2 different economics and 2 different psychology courses',
      'filter out course names that are seminar or research methods or special topics',
      'always return 5 more results than user requested in SQL query',
      'Economics major requirements: ECON050, ECON101, ECON102, ECON125, course codes in economics greater than 125',
      'Government major requirements: GOVT020, GOVT080, GOVT060 or GOVT070, 2 of (GOVT050 or GOVT055, GOVT112A or GOVT112B), course codes in government greater than 100',
      'History major requirements: course name focus on United States, course name focus on Europe, course name focus on Asia, Latin America, Africa, Middle East',
      'Psychology major requirements: PSYC030, PSYC037 or PSYC092, PSYC065 or PSYC070 or PSYC081, PSYC040 or PSYC096 or PSYC097, PSYC109, PSYC110 and PSYC111, course codes greater than 100 in psychology',
      'Philosophy major requirements: 1 course code less than 059, PHIL095, some history of philosophy course, some ethics course, PHIL198',
      'Data Science major requirements: CSCI004 or CSCI005 or CSCI040, MATH031, CSCI055 or MATH055, CSCI046, MATH060, CSCI036 or ECON122 or ECON160 or PSYC166, MATH151, MATH152, CSCI145, CSCI143, some ethics course',
      'Data Science sequence requirements: CSCI004 or CSCI005 or CSCI040, CSCI036 or ECON122 or ECON160 or PSYC166, ECON120 or GOVT055 or MATH052 or MATH152 or PSYC109, CSCI046 or ECON125 or MATH151 or PSYC111, CSCI143 or CSCI145 or ECON126 or MATH152 or MATH156 or MATH160 or MATH166 or MATH186 or MATH187 or PSYC167, DS180',
      'Math major requirements: MATH032, MATH060, MATH131, MATH151', 
      'Computer Science major requirements: CSCI060, MATH055, CSCI070, CSCI081, CSCI105, CSCI123, CSCI140, CSCI183, CSCI184, CSCI195',
      'When courses within major requirements are separated by an or, it means if one of the courses is taken taking another course within the or statement is not allowed',
  }

  # print('schema:', schema)
  return schema
    
def get_response(user_query: str, db: SQLDatabase, chat_history: list):
  schema = get_schema('lol')
  sql_query = get_sql_chain(user_query, schema, chat_history)
  # Remove backticks and `sql` tags if present
  sql_query = re.sub(r"```sql|```", "", sql_query).strip()
  # print('Cleaned SQL Query:', sql_query)
  
  try:
    db_file = 'lol'
    db = init_database(db_file)
    sql_response = db.run(sql_query)
    print(f"SQL Query: {sql_query}, Response: {sql_response}")
  except Exception as e:
    print(f"Error executing SQL Query: {e}")
    raise
  # sql_response = db.run(sql_query)
  # print(f"SQL Query: {sql_query}, Response: {sql_response}")
  
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