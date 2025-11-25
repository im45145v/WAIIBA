# Alumni Management System

A comprehensive system for managing alumni data with LinkedIn profile scraping, database storage, cloud PDF backup, and an NLP-powered chatbot interface.

## Features

- 🔍 **LinkedIn Scraping**: Automated scraping of LinkedIn profiles using Playwright
- 🗄️ **PostgreSQL Database**: Structured storage for alumni data including job and education history
- ☁️ **Cloud Storage**: Backblaze B2 integration for storing LinkedIn profile PDFs
- 🌐 **Web Interface**: Streamlit application for browsing, filtering, and exporting alumni data
- 🤖 **NLP Chatbot**: Natural language interface for querying alumni information
- 🔄 **Automation**: GitHub Actions workflow for periodic scraping every 6 months
- 🔐 **Secure**: All sensitive credentials managed via environment variables

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker & Docker Compose (for local database)
- A LinkedIn account (for scraping)
- A Backblaze B2 account (for PDF storage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/im45145v/WAIIBA.git
cd WAIIBA
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Start the local database (for testing)**:
```bash
docker-compose up -d
```

6. Initialize the database:
```bash
python -c "from alumni_system.database.init_db import init_database; init_database()"
```

7. Run the Streamlit application:
```bash
streamlit run alumni_system/frontend/app.py
```

## Local Database Setup (Testing Mode)

For local development and testing, use Docker Compose to spin up a PostgreSQL database:

```bash
# Start PostgreSQL database
docker-compose up -d

# The database will be available at:
# - Host: localhost
# - Port: 5432
# - Database: alumni_db
# - User: postgres
# - Password: alumni_dev_password

# To stop the database
docker-compose down

# To stop and remove all data
docker-compose down -v

# Optional: Start with pgAdmin UI for database management
docker-compose --profile admin up -d
# Access pgAdmin at http://localhost:5050
# Email: admin@alumni.local
# Password: admin123
```

Update your `.env` file for local testing:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alumni_db
DB_USER=postgres
DB_PASSWORD=alumni_dev_password
```

## How LinkedIn Login Works

The LinkedIn scraper uses Playwright (a browser automation library) to authenticate with LinkedIn. Here's how it works:

### Authentication Flow

1. **Browser Launch**: Playwright launches a Chromium browser instance (headless by default)
2. **Navigate to Login**: The scraper navigates to `https://www.linkedin.com/login`
3. **Enter Credentials**: Your LinkedIn email and password (from environment variables) are filled into the login form
4. **Submit Login**: The login button is clicked programmatically
5. **Verify Success**: The scraper checks if the URL changed to the feed page, indicating successful login

### Configuration

Set these environment variables in your `.env` file:

```bash
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Optional scraper settings
SCRAPER_HEADLESS=true          # Run browser in headless mode (no UI)
SCRAPER_SLOW_MO=100            # Milliseconds delay between actions
SCRAPER_MIN_DELAY=5            # Minimum delay between profile scrapes (seconds)
SCRAPER_MAX_DELAY=15           # Maximum delay between profile scrapes (seconds)
```

### Security Considerations

- **Dedicated Account**: Use a dedicated LinkedIn account for scraping, not your personal account
- **2FA Limitation**: If 2FA is enabled, the scraper cannot bypass security checkpoints automatically
- **Rate Limiting**: The scraper includes random delays to avoid triggering LinkedIn's anti-bot detection
- **Account Risk**: LinkedIn may suspend accounts that violate their Terms of Service
- **Checkpoint Handling**: If LinkedIn requires security verification (CAPTCHA, email verification), manual intervention is needed

### Troubleshooting LinkedIn Login

| Issue | Solution |
|-------|----------|
| Login fails immediately | Verify email/password are correct in `.env` |
| Security checkpoint triggered | Log in manually once to verify the account |
| Account suspended | Create a new dedicated account, use longer delays |
| 2FA required | Disable 2FA on the scraping account or handle manually |

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following:

| Variable | Description |
|----------|-------------|
| `DB_HOST` | PostgreSQL host (default: localhost) |
| `DB_PORT` | PostgreSQL port (default: 5432) |
| `DB_NAME` | Database name (default: alumni_db) |
| `DB_USER` | Database username |
| `DB_PASSWORD` | Database password |
| `LINKEDIN_EMAIL` | LinkedIn login email |
| `LINKEDIN_PASSWORD` | LinkedIn login password |
| `B2_APPLICATION_KEY_ID` | Backblaze B2 key ID |
| `B2_APPLICATION_KEY` | Backblaze B2 application key |
| `B2_BUCKET_NAME` | B2 bucket name for PDFs |

### GitHub Secrets (for automation)

For the GitHub Actions workflow, configure these repository secrets:

- `DB_PASSWORD`
- `LINKEDIN_EMAIL`
- `LINKEDIN_PASSWORD`
- `B2_APPLICATION_KEY_ID`
- `B2_APPLICATION_KEY`
- `B2_BUCKET_NAME`

## Project Structure

```
WAIIBA/
├── alumni_system/
│   ├── __init__.py
│   ├── chatbot/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── nlp_chatbot.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── connection.py
│   │   ├── crud.py
│   │   ├── init_db.py
│   │   └── models.py
│   ├── frontend/
│   │   ├── __init__.py
│   │   └── app.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── job.py
│   │   ├── linkedin_scraper.py
│   │   └── run.py
│   └── storage/
│       ├── __init__.py
│       ├── b2_client.py
│       └── config.py
├── .github/
│   └── workflows/
│       └── scraper.yml
├── scripts/
│   └── init_db.sql
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Usage

### Web Interface

The Streamlit application provides:

- **Dashboard**: Overview of alumni statistics
- **Browse Alumni**: Paginated view of all alumni records (includes previous companies column)
- **Search & Filter**: Filter by batch, company, location, or search by name
- **Alumni Details**: View detailed career history with past companies and roles
- **Chatbot**: Natural language queries about alumni
- **Admin Panel**: Add, edit, and delete alumni records

### Chatbot Queries

Example queries the chatbot can handle:

- "Who works at Google?"
- "Find alumni from batch 2020"
- "Show all software engineers"
- "How many alumni do we have?"
- "Alumni in Bangalore"

### Manual Scraping

Run the scraper manually:

```bash
python -m alumni_system.scraper.run --batch 2020 --max-profiles 50
```

Options:
- `--batch`: Filter by specific batch
- `--max-profiles`: Maximum profiles to scrape (default: 100)
- `--force-update`: Update all profiles regardless of last scrape time
- `--update-threshold-days`: Days threshold for updates (default: 180)

### Automated Scraping

The GitHub Actions workflow automatically runs:
- Every 6 months (January 1st and July 1st)
- Can be triggered manually via the Actions tab

## Database Schema

### Alumni Table
- Personal info (name, gender, batch, roll number)
- Contact info (emails, phone numbers)
- LinkedIn info (ID, URL, PDF URL)
- Current position (company, designation, location)
- Additional info (internships, higher studies, remarks)

### Job History Table
- Company name, designation, location
- Start/end dates
- Employment type
- Tracks all previous companies and roles

### Education History Table
- Institution, degree, field of study
- Start/end years
- Grade, activities

### Scraping Logs Table
- Scraping status and duration
- Error messages
- PDF storage status

## Security Considerations

- **Never commit** the `.env` file or any credentials to version control
- Use strong, unique passwords for all services
- Rotate credentials periodically
- Be mindful of LinkedIn's Terms of Service regarding scraping
- Enable 2FA on your LinkedIn account for security

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for educational purposes. Be aware of and comply with LinkedIn's Terms of Service when using the scraping functionality.

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running (`docker-compose ps`)
- Check environment variables are correctly set
- Ensure the database exists

### Scraping Issues
- LinkedIn may block scraping attempts; use reasonable delays
- Security checkpoints may require manual intervention
- Consider using a residential proxy for better reliability

### B2 Storage Issues
- Verify B2 credentials are correct
- Ensure the bucket exists and has proper permissions
- Check file size limits
