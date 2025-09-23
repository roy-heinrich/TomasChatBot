#!/usr/bin/env python3
"""
Test questions generated from actual database content
"""

TEST_QUESTIONS = [
    {
        "question": "Where is the guidance office?",
        "category": "direct",
        "expected_keywords": ["where", "database"]
    },
    {
        "question": "Location of the school",
        "category": "direct",
        "expected_keywords": ["location", "database"]
    },
    {
        "question": "Where is the school located?",
        "category": "variation",
        "expected_keywords": ["where", "database"]
    },
    {
        "question": "Saan ang paaralan?",
        "category": "tagalog",
        "expected_keywords": ["saan", "database"]
    },
    {
        "question": "comfort room, cr",
        "category": "direct",
        "expected_keywords": ["comfort", "database"]
    },
    {
        "question": "flag cermony",
        "category": "direct",
        "expected_keywords": ["flag", "database"]
    },
    {
        "question": "gmail, email",
        "category": "direct",
        "expected_keywords": ["gmail,", "database"]
    },
    {
        "question": "Grade level",
        "category": "direct",
        "expected_keywords": ["grade", "database"]
    },
    {
        "question": "Head Teacher",
        "category": "direct",
        "expected_keywords": ["head", "database"]
    },
    {
        "question": "Who is the head teacher?",
        "category": "variation",
        "expected_keywords": ["who", "database"]
    },
    {
        "question": "Sino ang head teacher?",
        "category": "tagalog",
        "expected_keywords": ["sino", "database"]
    },
    {
        "question": "Principal",
        "category": "direct",
        "expected_keywords": ["principal", "database"]
    },
    {
        "question": "What is Tomas SM. Bautista Elementary School?",
        "category": "direct",
        "expected_keywords": ["what", "database"]
    },
    {
        "question": "Does the school use report cards or online grading?",
        "category": "direct",
        "expected_keywords": ["does", "database"]
    },
    {
        "question": "Rules for wearing IDs inside the school.",
        "category": "direct",
        "expected_keywords": ["rules", "database"]
    },
    {
        "question": "What is the schools class schedule?",
        "category": "direct",
        "expected_keywords": ["what", "database"]
    },
    {
        "question": "What grade levels are offered at the school?",
        "category": "direct",
        "expected_keywords": ["what", "database"]
    },
    {
        "question": "How can i contact the school office?",
        "category": "direct",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "Does the School have a Facebook page or website?",
        "category": "direct",
        "expected_keywords": ["does", "database"]
    },
    {
        "question": "History",
        "category": "direct",
        "expected_keywords": ["history", "database"]
    },
    {
        "question": "Are transferees accepted?",
        "category": "direct",
        "expected_keywords": ["are", "database"]
    },
    {
        "question": "How many sections are there per grade level?",
        "category": "direct",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "Does the school offer Special education (SPED) classes?",
        "category": "direct",
        "expected_keywords": ["does", "database"]
    },
    {
        "question": "What organizations or clubs are available for students?",
        "category": "direct",
        "expected_keywords": ["what", "database"]
    },
    {
        "question": "Does the school have a feeding Program?",
        "category": "direct",
        "expected_keywords": ["does", "database"]
    },
    {
        "question": "How much are the school fees?",
        "category": "variation",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "Magkano ang tuition?",
        "category": "tagalog",
        "expected_keywords": ["magkano", "database"]
    },
    {
        "question": "Does the school have a library?",
        "category": "direct",
        "expected_keywords": ["does", "database"]
    },
    {
        "question": "Are there security guards in the school?",
        "category": "direct",
        "expected_keywords": ["are", "database"]
    },
    {
        "question": "Does the school participate in inter-school competitions?",
        "category": "direct",
        "expected_keywords": ["does", "database"]
    },
    {
        "question": "How school events announced to parents?",
        "category": "direct",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "re there Remedial or tutorial classes offered?",
        "category": "direct",
        "expected_keywords": ["re", "database"]
    },
    {
        "question": "How do teachers communicate with parents",
        "category": "direct",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "When was this school established?",
        "category": "direct",
        "expected_keywords": ["when", "database"]
    },
    {
        "question": "student population this year",
        "category": "direct",
        "expected_keywords": ["student", "database"]
    },
    {
        "question": "Vision Mission and Core Values",
        "category": "direct",
        "expected_keywords": ["vision", "database"]
    },
    {
        "question": "school canteen",
        "category": "direct",
        "expected_keywords": ["school", "database"]
    },
    {
        "question": "Is there a computer laboratory?",
        "category": "direct",
        "expected_keywords": ["is", "database"]
    },
    {
        "question": "What is the grading system used by the school?",
        "category": "direct",
        "expected_keywords": ["what", "database"]
    },
    {
        "question": "Does the school sell PE uniforms",
        "category": "direct",
        "expected_keywords": ["does", "database"]
    },
    {
        "question": "School rules on Gadget",
        "category": "direct",
        "expected_keywords": ["school", "database"]
    },
    {
        "question": "Where i can buy the school uniform",
        "category": "direct",
        "expected_keywords": ["where", "database"]
    },
    {
        "question": "How do teachers  communicate with parents?

",
        "category": "direct",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "How does the school handle late enrollees?",
        "category": "direct",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "What are the major annual school activities?",
        "category": "direct",
        "expected_keywords": ["what", "database"]
    },
    {
        "question": "Earthquake drill and Fire drill",
        "category": "direct",
        "expected_keywords": ["earthquake", "database"]
    },
    {
        "question": "How many teachers are currently in the school?",
        "category": "direct",
        "expected_keywords": ["how", "database"]
    },
    {
        "question": "School Division Superintendent",
        "category": "direct",
        "expected_keywords": ["school", "database"]
    },
    {
        "question": "OIC, Asst. Schools division superintendent",
        "category": "direct",
        "expected_keywords": ["oic,", "database"]
    },
    {
        "question": "Public Schools district Supervisor",
        "category": "direct",
        "expected_keywords": ["public", "database"]
    },
    {
        "question": "Kindergarten Adviser",
        "category": "direct",
        "expected_keywords": ["kindergarten", "database"]
    },
    {
        "question": "Grade 1 Adviser",
        "category": "direct",
        "expected_keywords": ["grade", "database"]
    },
    {
        "question": "Grade 2 Adviser",
        "category": "direct",
        "expected_keywords": ["grade", "database"]
    },
    {
        "question": "Grade 3 Adviser",
        "category": "direct",
        "expected_keywords": ["grade", "database"]
    },
    {
        "question": "Grade 5 Adviser",
        "category": "direct",
        "expected_keywords": ["grade", "database"]
    },
    {
        "question": "Grade 4 Adviser",
        "category": "direct",
        "expected_keywords": ["grade", "database"]
    },
    {
        "question": "Grade 6 Adviser",
        "category": "direct",
        "expected_keywords": ["grade", "database"]
    },
    {
        "question": "Learning Support Aide",
        "category": "direct",
        "expected_keywords": ["learning", "database"]
    },
]

def get_test_questions():
    """Return all test questions"""
    return TEST_QUESTIONS

def get_questions_by_category(category):
    """Return questions filtered by category"""
    return [q for q in TEST_QUESTIONS if q["category"] == category]
