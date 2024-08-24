# Fantasy Draft Assistance

This repository contains the backend code for the "Fantasy Draft Assistance" custom GPT agent, designed to help you manage your fantasy football league. The Flask API serves various endpoints that interact with ESPN Fantasy Football data, providing insights like available players, best available players, projected winners, and more.

## Features

- **Get Available Players**: Retrieve a list of available players filtered by position.
- **Get Best Available Player**: Find the best available player based on draft data.
- **Suggest Next Pick**: Get suggestions for your next pick in the draft.
- **Get Current Roster**: View the current roster based on real-time data.
- **Get Draft Summary**: Get a summary of the draft so far.
- **Get Projected Winner**: Analyze teams and determine who is likely to win the league.

## Prerequisites

Before you start, ensure you have the following installed on your system:

- Python 3.8+
- `pip` (Python package installer)
- `venv` (Python virtual environment)
- `flyctl` (Fly.io CLI)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/odiosdado/gpt-fantasy-football.git
cd gpt-fantasy-football
```
### 2. Create and Activate a Virtual Environment
It's recommended to use a virtual environment to manage dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
With the virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
You need to set the following environment variables to configure the Flask application:

```bash
export LEAGUE_ID="your_league_id"
export SEASON_ID="your_season_id"
export ESPN_S2="your_espn_s2_token"
export SWID="your_swid_token"
export SCORING="PPR"  # Example: PPR (Point Per Reception) scoring system
```
Make sure these environment variables are set in your environment. You can add them to a .env file for local development.

### 5. Run the Flask Application
To start the Flask application locally, run:

``` bash
flask run
By default, the API will be accessible at http://localhost:5000.
```

### 6. Deploying to Fly.io
To deploy the application to Fly.io, follow these steps:

Install Flyctl: If you haven't installed flyctl yet, follow the instructions here.

Login to Fly.io:

```bash
flyctl auth login
```
Create and Deploy Your App:

```bash
flyctl launch
```
Follow the prompts to set up your app on Fly.io. Choose to deploy immediately if prompted.
Set Environment Variables on Fly.io:
After deploying, you'll need to set the environment variables in Fly.io:

```bash
flyctl secrets set LEAGUE_ID="your_league_id" SEASON_ID="your_season_id" ESPN_S2="your_espn_s2_token" SWID="your_swid_token" SCORING="PPR"
```

### 7. Create Your Custom GPT Agent
1. To create your own Custom GPT agent using this Flask API, follow these steps:
1. Access the OpenAI Platform: Visit the OpenAI platform and log in to your account.
1. Create a New GPT Agent:
1. Go to the Custom GPTs section and create a new GPT.
1. Use the provided OpenAPI schema (from this repository) to define the API that the GPT agent will interact with.
1. Configure the API:
1. Set the API base URL to your deployed Fly.io application.
1. Map the API endpoints to the GPT’s functionalities (e.g., retrieving player data, suggesting picks).
1. Test Your Agent: Use the testing interface to ensure your GPT agent interacts correctly with the Flask API.

### 8. Testing the API
You can test the API endpoints locally or using tools like Postman or Curl:

Example to get available players:

```bash
curl -X GET "http://localhost:5000/get-available-players?position=RB" -H "Authorization: Bearer YOUR_TOKEN"
```

### 9. Contributing
Contributions are welcome! Please fork the repository and submit a pull request for any improvements or fixes.

### 10. License
This project is licensed under the MIT License. See the LICENSE file for details.