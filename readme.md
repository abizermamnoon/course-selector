# Overview
The Claremont Colleges has web apps such as hyperschedule and 5C scheduler to build their course schedules for each semester. I wanted to build a web app powered by generative AI that would reduce the effort that students need to put in to build these schedules. Students just have to provide the chatbot with the courses they have taken and the major they are interested in pursuing. The chatbot can provided the user with courses that they can take.

# Features
**Feature 1: Personalized Course Recommendations**
Students can input the courses they've taken, specify their major, and indicate the subjects they wish to study next semester. The chatbot suggests courses that satisfy their major requirements and explore additional interests.
Example 1: 
User Query: 
```
I am a government major. I have taken GOVT020, GOVT060 and GOVT070. Next semester, I want to take two government courses, 1 philosophy GE course and 1 psychology GE course. Can you recommend courses I can take given my pre-reqs?
```
Response: 
```
Based on your prerequisites and the courses you've already taken as a government major, here are some recommendations for the next semester:

Government Courses:

GOVT055 - Empirical Methods: Instructor: Shanna Rose. Scheduled for Tuesdays and Thursdays from 1:15 PM to 2:30 PM at CM Campus, The Kravis Center, 165. This course covers the philosophy and practice of political science research. Prerequisite: Introduction American Politics.
GOVT080 - Intro to Political Philosophy: Instructor: Mark Blitz or Ioannis Evrigenis. Available on Tuesdays and Thursdays from either 11:00 AM to 12:15 PM or 1:15 PM to 2:30 PM at CM Campus. This course introduces various philosophical understandings of political life.
Philosophy GE Course:

PHIL030 - Intro: Philosophical Questions: Instructors include Suzanne Obdrzalek, Alex Rajczi, or Briana Toole. Offered at various times, including Tuesdays and Thursdays from 11:00 AM to 12:15 PM, 1:15 PM to 2:30 PM, or 2:45 PM to 4:00 PM; and Monday and Wednesday from 3:00 PM to 5:00 PM at CM Campus. The course focuses on teaching philosophy through historical texts or contemporary readings, depending on the instructor.
Psychology GE Course:

PSYC030 - Introduction to Psychology: Instructors Alison M. Harris or Daniel A. Krauss. Scheduled on Tuesdays and Thursdays from 1:15 PM to 2:30 PM or 2:45 PM to 4:00 PM, and Monday and Wednesday from 8:10 AM to 9:25 AM or 9:35 AM to 10:50 AM at CM Campus. This course surveys major areas of scientific psychology.
These courses were selected based on their relevance to your major and the requirement to fulfill your GE needs. Generally, they are offered every semester or year, fitting well into your schedule at CMC.
```

**Feature 2: Career-Aligned Course Recommendations**
Student can input the raw job description they want to apply to and ask the chatbot courses they can take to situate themselves better among other candidates

User Query:
```
I am interested in this policy role. Here is the job description:

For five decades, the Environmental Law Institute (ELI) has played a pivotal role in shaping the fields of environmental law, policy, and management, both domestically and internationally.  ELI is hiring interns to support the research and publications departments of the Institute. Interns work directly with staff attorneys, editors, scientists, and policy analysts on a variety of projects. Substantive areas of focus in local, regional, federal, and international policy and law include: climate change, green technology, land use, biodiversity, air quality, public health, hazardous waste and brownfields, wetlands and watersheds, armed conflict and the environment, environmental management systems, public participation, environmental justice, Indigenous issues, and environmental enforcement. ABOUT THE INTERNSHIP Interns conduct in-depth secondary and primary research, attend and report on outside events, analyze, edit, and synthesize scholarly material, assist with preparation for environmental training courses, and provide limited administrative support. ELI integrates interns into the day-to-day operations of the Institute, and interns are encouraged to attend ELI-sponsored workshops, seminars, roundtable, and other events. In addition, interns will develop and complete an independent research project under the guidance of ELI staff. QUALIFICATIONS Eligibility is limited to students enrolled in an undergraduate program who have at least completed their first year of college. Applicants are ineligible if they graduate from college/university before or during this summer 2025 internship. Candidates should possess superior research, writing, and interpersonal communication skills, as well as a deep desire to gain knowledge of the environmental field. A strong academic background is required, but specific environmental experience is not. Candidates should demonstrate self-awareness, cultural competency and inclusivity, the ability to work with colleagues and stakeholders across diverse cultures and backgrounds, and the willingness to learn new digital tools. ABOUT ELI The Environmental Law Institute (ELI) is an environmental law, science, and policy center that makes law work for people, places, and the planet. We envision a healthy environment, prosperous economies, and vibrant communities founded on the rule of law. Our mission is to foster innovative, just, and practical law and policy solutions to enable leaders across borders and sectors to make environmental, economic, and social progress. ELI’s Research and Policy experts develop innovative legal and governance solutions to challenges in areas such as climate change; environmental justice; natural resource management; land conservation and smart growth; biodiversity loss and habitat destruction; and air, water, and soil pollution. Together, ELI’s staff aims to: Build the skills and capacity of tomorrow’s leaders and institutions Research and analyze complex and pressing environmental challenges Promote and disseminate the best thinking through print and electronic media Work with partners to develop and implement laws, policies, and other means to protect the environment and society Convene people with diverse perspectives to build understanding through robust dialogue For more information on ELI’s programs, visit https://www.eli.org/programs. COMPENSATION & PROGRAM REQUIREMENTS ELI will provide interns an hourly wage of $18.00. If an intern desires to receive course credit for the internship and the intern’s school prohibits earning income for the same work as the course credit is being received, accommodations can be made. Candidates for the summer internship must be available to work approximately 37.5 hours/week for at least 10 consecutive weeks from June to August 2025. This is a hybrid internship experience. Therefore, you must be physically present in the DC metro area (where ELI’s office is located).
What courses should I take to make myself a better candidate?
```

Response:
```
Based on the internship description from the Environmental Law Institute (ELI), here are some courses that could be beneficial to make you a stronger candidate for the role:

Policy Lab (ECON100 CM-01)

Instructor: Eric Helland
Schedule: Monday and Wednesday from 1:15 PM to 2:30 PM
Location: CM Campus, Center Court, TNT1Courser, Zachary C.
Description: This course focuses on the politics and process of domestic policymaking in the United States using an experiential approach to policy research and formation. Prerequisites include Introduction to American Politics and Principles of Economic Analysis.
Policy Lab (GOVT100 CM-01)

Instructor: Eric Helland
Schedule: Monday and Wednesday from 1:15 PM to 2:30 PM
Location: CM Campus, Center Court, TNT1Courser, Zachary C.
Description: Similar to ECON100, this course explores domestic policymaking with a focus on analytical tools and case studies. Prerequisites are Introduction to American Politics and Principles of Economic Analysis.
Intl Political Feature Writing (GOVT142 CM-01)

Instructor: William Ascher
Schedule: Monday and Wednesday from 2:45 PM to 4:00 PM
Location: CM Campus, The Kravis Center, LC63
Description: A course on journalistic writing about international politics, covering topics like migration and pollution. Prerequisite is Introduction to American Politics.
U.S. Politics and Social Policy (GOVT152C CM-01)

Instructor: Dionne Bensonsmith
Schedule: Tuesday and Thursday from 2:45 PM to 4:00 PM
Location: CM Campus, Bauer Center, 2
Description: Examines U.S. social policy with a focus on education, healthcare, and welfare policy.
Cold War America (HIST099 CM-01)

Instructor: Lily Geismer
Schedule: Tuesday and Thursday from 1:15 PM to 2:30 PM
Location: CM Campus, The Kravis Center, 103
Description: Provides an overview of U.S. history during the Cold War era, focusing on historical analysis, research, and writing.
Monetary and Fiscal Policy (ECON140 CM-01)

Instructor: Madison Florian Pascal
Schedule: Tuesday and Thursday from 9:35 AM to 10:50 AM
Location: CM Campus, Bauer Center, 25
Description: Investigates monetary and fiscal policy in market economies, understanding welfare effects of policy interventions. Prerequisite is Intermediate Macroeconomics.
Seminar in Research Methods (ECON180 CM-01)

Instructor: Richard Burdekin
Schedule: Tuesday from 11:00 AM to 12:15 PM
Location: CM Campus, Bauer Center, 36
Description: This seminar aids in the preparation of a senior thesis in economics and is recommended for all economics majors.
These courses focus on policy, research, and writing, aligning well with the core skills required for the internship. They also provide a comprehensive understanding of policy-making processes and research methods, which are crucial for a role at ELI.
```

# Project Setup

**STEP 1: Install Required Packages**

```
$ pip install -r requirements.txt
```

**STEP 2: Set Up API Key**

Create a .env file in src folder. Generate an API key and add the API key within the file
```
OPENAI_API_KEY=your_api_key_here
```

**STEP 3: Run the Application**

```
$ streamlit run src/app.py

```
