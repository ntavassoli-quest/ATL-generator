# ATL Activity Generator

Upload a class text (grades 9-12) and get:

* **Teacher ATL** - student pages, running-record copy with 100-word markers, vocabulary targets,
  rubrics, full-credit answers, writing observations and a score report
* **Student ATL** - student-facing pages with no answers or scoring, plus the teacher running-record
  copy as the last page (remove it before handing the packet out)

Each comes as a **PDF** (for printing) or **Word** file (for editing). Uploads can be PDF, Word, .txt or .md.

## Run it on your own computer (Mac)

    cd ~/Desktop/atl_generator
    pip3 install -r requirements.txt
    export ANTHROPIC_API_KEY=paste-your-key-here
    python3 -m streamlit run app.py

Optional: `export APP_PASSWORD=something` to ask for a password.

## Put it online for your team (Streamlit Community Cloud)

1. Create a free GitHub account and a new **private** repository.
2. Upload these files to it: `app.py`, `atl_generator.py`, `requirements.txt`, `.gitignore`
   (do not upload your API key).
3. Go to share.streamlit.io, sign in with GitHub, and click **Create app**. Pick the repository,
   branch `main`, and main file `app.py`.
4. Before deploying, open **Advanced settings -> Secrets** and paste:

        ANTHROPIC_API_KEY = "sk-ant-your-key"
        APP_PASSWORD = "choose-a-team-password"

5. Click **Deploy**. You get a link like `https://your-app.streamlit.app`.
   Share the link and the password with your team. They need no accounts.

## Keep it safe and affordable

* **Always set APP_PASSWORD.** Without it anyone with the link can run up your API bill.
* In the Anthropic console, set a **monthly spend limit** on the key.
* Only paste the class reading. Never student names or student work.
* The reading text goes through the hosting service and the Anthropic API. Check with your
  school's IT / privacy contact before using it with your team.
* The PDF uses built-in fonts, so text outside Western European languages may not display.

## Command line

    python atl_generator.py reading.pdf --title "My Text" --grade 10 --mode student --format pdf
