# LinkedIn Deep Scrape Report - Ingecart Posts

Date: 2026-05-06
Target URL: https://www.linkedin.com/company/ingecart/posts/?feedView=all
Scope: Public-access scrape without authenticated LinkedIn session

## 1) Executive Result
A deep scrape of the LinkedIn posts feed could not retrieve post-level content due LinkedIn access controls (sign-in wall and anti-scraping restrictions on guest sessions). The target page and related endpoints return login-gated content or non-extractable responses for anonymous access.

## 2) Verified Publicly Accessible Findings
From the accessible company page endpoint:
- Company page URL: https://www.linkedin.com/company/ingecart/
- Access behavior: prompts sign-in to view profile details and network context
- Public asset recovered:
  - Company logo URL:
    - https://media.licdn.com/dms/image/v2/D4D0BAQEQPcyOF3WIAA/company-logo_200_200/company-logo_200_200/0/1733900598808/ingecart_logo?e=2147483647&v=beta&t=aHdppOvhHLlAGowivSVnDxueFXgz1C1RjLpJTz-Iw6o

## 3) Attempt Matrix
Attempted URLs and result:
- https://www.linkedin.com/company/ingecart/posts/?feedView=all
  - Result: sign-in page (no posts returned)
- https://www.linkedin.com/company/ingecart/posts/
  - Result: no meaningful extractable content
- https://www.linkedin.com/company/ingecart/posts/?feedView=all&viewAsMember=true
  - Result: no meaningful extractable content
- https://www.linkedin.com/company/ingecart/
  - Result: sign-in wall + public logo image URL visible

## 4) What Could Not Be Extracted Without Login
Not reliably available in anonymous mode:
- Post text bodies
- Post dates and chronology
- Engagement metrics (likes/comments/reposts)
- Hashtags and outbound links per post
- Media sets attached to posts (images/video/documents)

## 5) Recommended Path For Full Post-Level Deep Research
To generate the same depth as the website report for LinkedIn posts, run an authenticated export workflow:
1. Open LinkedIn in a logged-in browser profile.
2. Visit the company posts feed and scroll to load historical posts.
3. Capture page content using a browser export method (HTML save or structured extraction script).
4. Parse loaded post cards for:
   - post id/url
   - publish date
   - text content
   - hashtags
   - media urls/types
   - engagement counters
5. Save into normalized JSON and a summarized Markdown report.

## 6) Ready-to-Use Research Summary (for immediate use)
Current confidence summary:
- LinkedIn content visibility is gated for this company feed under anonymous access.
- Publicly verified artifact: official company logo URL.
- Full deep post analytics requires authenticated scraping context or exported source data.

## 7) Next-Step Deliverable Available
Once authenticated source HTML/JSON is provided, I can produce:
- full post archive table
- topic clustering by month
- engagement trend summary
- top-performing content themes
- media library with downloadable links
