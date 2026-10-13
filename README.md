# Irriki Tourism Auto-Blogging Bot (irrikitourism.com)

Automated SEO blog writer & WordPress publisher powered by GitHub Models / OpenAI and GitHub Actions for **Irriki Tourism**.

## Setup Instructions:

1. Create a new repository on GitHub (e.g. `irriki-autoblog`) and push all files inside this `irriki-autoblog` folder to it.
2. In your GitHub repository, go to **Settings > Secrets and variables > Actions**.
3. Click **New repository secret** and add these 3 secrets:
   - `WP_URL`: `https://irrikitourism.com`
   - `WP_USERNAME`: Your WordPress admin username
   - `WP_APP_PASSWORD`: Your WordPress Application Password (create one in **WP Admin > Users > Profile > Application Passwords**)
4. Go to the **Actions** tab in GitHub, select **Automated Daily Irriki Tourism Blog Post**, and click **Run workflow** to publish your first article immediately!
