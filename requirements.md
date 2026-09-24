# Job Application Automation Requirements

## User Profile

- Name and contact details
- Location and preferred work locations
- Skills and technologies
- Years of experience
- Education and certifications
- Employment history
- Notice period
- Expected salary
- Preferred job titles and industries
- Resume and cover letter files
- Job inclusion and exclusion keywords

## Job Matching

- Match jobs against skills, experience, location, salary, and job title
- Configurable minimum match score
- Include and exclude keyword rules
- Duplicate job detection
- Company and recruiter filtering
- Remote, hybrid, and onsite preferences
- Seniority-level filtering

## Platform Integration

- Separate integration modules for LinkedIn and Naukri
- Platform login and session management
- Job search and job-detail retrieval
- Application form detection
- Resume upload support
- Common-question answer support
- Application status tracking
- Platform-specific configuration
- Handling of expired sessions, login challenges, CAPTCHA, and MFA

## Security and Privacy

- Never store passwords in source code
- Never store passwords in plain text
- Use environment variables or a secrets manager
- Encrypt stored credentials and session data
- Protect resumes and personal information
- Exclude credentials, logs, databases, and private files from version control
- Support credential deletion and account logout
- Do not log passwords, tokens, or sensitive personal data
- Maintain an audit trail for application activity