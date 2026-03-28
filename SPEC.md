## Behavior: 
- From the user's perspective, this app will first introduce the functionality (quizzing) to the user, then ask how many questions they'd like to be tested on. Then, the app should randomly select that many questions from its internal question bank. 

## Data format:
```json
{
  "questions": [
    {
      "question": "What is the efficiency of checking membership in a set in Python",
      "type": "multiple_choice",
      "options": ["O(n)", "O(n^2)", "O(log n)", "O(1)"],
      "answer": "O(1)",
      "category": "Efficiency",
      "difficulty": "Easy"
    },
    {
      "question": "How many passes will selection sort make on a list of length 8?",
      "type": "multiple_choice",
      "options": ["80", "1", "8", "3"],
      "answer": "8",
      "category": "Efficiency",
      "difficulty": "Medium"
    },
     {
      "question": "How many passes will merge sort make on a list of length 8?",
      "type": "multiple_choice",
      "options": ["80", "1", "8", "3"],
      "answer": "3",
      "category": "Efficiency",
      "difficulty": "Medium"
    },
      {
      "question": "If on a given computer, a function that runs in O(N) takes 10 seconds to run on a list with 1000 values, roughly how long will it take to run on the same computer for a list with 5000 values?",
      "type": "multiple_choice",
      "options": ["50 seconds", "10 seconds", "20 seconds", "2500 seconds"],
      "answer": "50 seconds",
      "category": "Efficiency",
      "difficulty": "Medium"
    },
    {
      "question": "What is the maximum number of indices that binary search would need to access when run on a list of length 64?",
      "type": "multiple_choice",
      "options": ["16", "8", "6", "4"],
      "answer": "6",
      "category": "Efficiency",
      "difficulty": "Hard"
    }
  ]
}
```

## File structure: 
- main.py to handle the interactions with the user and logic for showing questions, performance.py to handle creating the secure score history file with relevant statistics, and a JSON file with question bank

## Error handling: 
- If the JSON file is missing, display a message to the user and do not crash. If a user inputs invalid questions/syntax into the JSON question bank, similarly display a message. If a user misformats their answer, give them additional chances until they do it correctly. 

## Required features: 
- After one round of a quiz, the user must enter a username and a password. This app should have a local login system to manage this. Once logged in, users will be able to access more features, such as information on their performance, the ability to give feedback on whether they liked a question or not (which should influence what kinds of questions they see), and ability for users to modify questions in a human-readable json file. Performance should be tracked in a score history file that is not human-readable. It should also contain any other useful statistics that would help the user study. 

## Extension feature: 
- Additionally, users should be able to add difficulty tags to questions so that when they ask for questions to be quizzed on, they can filter by questions of a certain difficulty. This difficulty should affect their proficiency score, which should be calculated in the score history/performance file. 

## Acceptance criteria: 
- To check if this implementation is completed and successful, the following criteria must be met:

- 1. User is introduced to the app and allowed to test out a few questions
- 2. Then, the user is prompted to enter a username and password or to register. This system must be robust and make use of a local login system.
- 3. Users should be able to easily get information on their performance
- 4. Performance files must be secure and not human-readable
- 5. Users should be able to filter questions of certain difficulties. Proficiency statistics must consider the difficulty of the questions attempted.
- 6. Error handling must be robust and not crash on invalid or misformatted files/inputs as described above.
- 7. There should be no use of HTML, CSS, JavaScript, GUIs, or any APIs. 



