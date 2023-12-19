
# Nutaku™ King of Kinks Game Auto-Clicker Instruction Manual

---

### Windows
1. Please follow the [official guide](https://learn.microsoft.com/en-us/windows/python/beginners#install-python) to install Python3 on your Windows desktop
> Install Python3 from Microsoft Store application is **strongly recommended**.
2. Open the `subscribers.csv` file with any text editor, then follow CSV header and append your player account information at line 2.
    - Example
    ```csv
    platform,name,nutaku_id,user_id
    nutaku,JohnDoe,1234567,1010000012345
    ```
3. Open the Windows terminal application **(cmd, powershell, windows terminal .etc)**, and run `pip install requests` command to install required module for the project.
4. Change directory to the project root with `cd` command, then start the script depending on the event type.
    - For Clicker 2 event, run `python EventManager.py` command, the auto-clicker will provide the following services:
        - Collect wine item from player brewer at **~90% capacity**.
        - Upgrade player brewer while required materials are available.
        - Perform clickers by consuming all available wine items.
        - Player is required to **manually** answer all dialect windows during chapter storyline, all answers can be found in [here](https://kingofkinks.miraheze.org/wiki/EventClicker2).
        - Claim chapter reward once the clicker reaches 100% progression.
    - For Clicker 2.5 event, run `python MultiverseEvenManager.py`command, the auto-clicker will provide the following services:
        - Collect energy from player armband at **~90% capacity**.
        - Player is required to **manually** upgrade his armband if available. *TODO: Automate this process.*
        - Player is required to **manually** answer all dialect windows during chapter storyline, all answers can be found in [here](https://kingofkinks.miraheze.org/wiki/Dating_Event).
        - Player is required to **manually** claim rewards from each stage when completed. *TODO: Automate this process.*
> Do not close the terminal windows while running the script, otherwise the auto-clicker will stop the service.

---

### DISCLAIMER
This project is made by players from unofficial game [discord](https://discord.gg/king-of-kinks). We are in no way affiliated with Nutaku Games™, Nutaku Publishing™ or the developers of King of Kinks™.
