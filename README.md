# Nutaku™ King of Kinks Game Auto-Clicker

### User Manual
---

#### Windows

1. Please follow the [official guide](https://learn.microsoft.com/en-us/windows/python/beginners#install-python) to install Python3 on your desktop.
> Install Python3 from Microsoft Store is **strongly recommended**.
2. Open`subscribers.csv` file with any text editor, then follow CSV header and append your player account information at line 2.
    - Example
    ```csv
    platform,name,nutaku_id,user_id
    nutaku,JohnDoe,1234567,1010000012345
    ```
3. Open the terminal **(cmd, powershell, windows terminal .etc)**, and change directory to project root with `cd` command.
4. Run `pip install -r requirements.txt` command to install dependencies, then proceed to start the script by the event category,
    - **Clicker 2 Event**, run `python EventManager.py` command.
    - **Clicker 2.5 Event**, run `python MultiverseEventManager.py` command.

| :exclamation:    Do not close the terminal window while running the script, otherwise the program will be terminated. |
|-----------------------------------------------------------------------------------------------------------------------|

### Features

- Clicker 2 Event: `EventManager.py`
    - [x] Collect wine item from player brewer at **~90% capacity**.
    - [x] Upgrade player brewer if available.
    - [x] Perform clickers by consuming all available wine items each time.
    - [ ] Story chapter dialogue completion, all answers can be found in the [wiki](https://kingofkinks.miraheze.org/wiki/EventClicker2).
    - [x] Claim chapter reward once the clicker reaches 100% progression.
- Clicker 2.5 Event: `MultiverseEventManager.py`
    - [x] Collect energy from player armband at **~90% capacity**.
    - [ ] Upgrade player armband if available.
    - [ ] Story chapter dialogue completion, all answers can be found in the [wiki](https://kingofkinks.miraheze.org/wiki/Dating_Event).
    - [ ] Claim chapter rewards after stage completed.

### DISCLAIMER
---

This project is made by players from unofficial game [discord](https://discord.gg/king-of-kinks). We are in no way affiliated with Nutaku Games™, Nutaku Publishing™ or the developers of King of Kinks™.
