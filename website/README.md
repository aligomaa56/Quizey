# Quizey Website
Welcome to the Quizey website repository! This project is designed to provide an engaging and interactive platform for quizzes.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Contact](#contact)

## Introduction

Quizey is a web application that allows teachers, professors, or anyone who wants to create an exam and share it with others via a link. It aims to make learning fun and interactive. Whether you're a student looking to test your knowledge, a teacher creating exams for your class, or just someone who loves trivia, Quizey has something for you.

## Features

- **Robust API**: Provides a comprehensive set of endpoints for managing quizzes and exams.
- **Create and customize quizzes and exams**: Add your own questions and answers via API requests.
- **Share quizzes and exams with others**: Generate shareable links for your quizzes and exams.
- **Question Bank**: Each teacher can create their own question bank and store questions for future exams.
- **Track performance**: Retrieve performance data through API endpoints.
- **Secure and scalable**: Built with security and scalability in mind.
- **Multiple question formats**: Supports multiple-choice, true/false, and short answer questions.
- **Leaderboard**: Access leaderboard data to see rankings.
- **Timer**: Implement timers for quizzes and exams to increase the challenge.
- **Multiple Attempts**: Providing students with the option to take the exam multiple times as determined by the teacher.


## Installation

To get started with the Quizey website, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/aligomaa56/Quizey.git
    ```
2. Navigate to the project directory:
    ```bash
    cd Quizey/
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Obtain Google OAuth 2.0 credentials:
    1. Go to [Google Cloud Console](https://console.cloud.google.com/).
    2. Create a new project.
    3. Enable the Gmail API for your project.
    4. Create OAuth 2.0 credentials and download the `credentials.json` file.
    5. Place the `credentials.json` file in the root of your project directory(website).
## Usage

To start the development server, run:
```bash
python3 website/app.py
```
Open your browser and navigate to `http://localhost:5000` to view the website. Alternatively, you can use Postman to test the API, which is considered the best practice.

## Contributing

We welcome contributions! However, please note that the project is currently under development.

- **Report bugs**: If you find a bug, please report it.
- **Suggest features**: If you have an idea for a new feature, let us know.
- **Submit pull requests**: If you have a fix or a new feature, submit a pull request.

## Contact

If you have any questions or feedback, please don't hesitate to reach out. You can contact us at:
- **Alaa Badawy**: [alaa.badawy404@gmail.com](mailto:alaa.badawy404@gmail.com)
- **Ali Gomaa**: [alielsayedgomaa@gmail.com](mailto:alielsayedgomaa@gmail.com)

Thank you for visiting the Quizey website repository. We hope you enjoy using our platform!
