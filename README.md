# Portainer Compose Backup 🐳

Portainer centralizes your Compose projects, but that also means there's a single point of failure - losing access to all your stacks with just one accidental deletion or daemon crash! Since Portainer doesn't have a native backup solution, this project helps you securely store & track your compose files from multiple endpoints into a Git repository. It's saved my sanity (and data) on more than one occasion!

**You may use this as a template repository to begin with.**

## Overview 📋

- This Python script is used to backup Docker compose scripts created within Portainer to our project directory. The copies will be saved in a directory structure of the following format: `backups/[current year]/[current month]/[current date]/[endpoint]/[docker stack name]`. Once the copying operation is complete, the changes will be committed and pushed to Git.
- `db-exporter/` is a small Docker image (may need to be built) to export few necessary buckets from Portainer's BoltDB. This janky combination of using this `compose_backup.py` with `db-exporter\docker-compose.yml` is because there isn't a reliable BoltDB client for Python.
- Automatically maps `docker-compose.yml` files to their respective Portainer endpoints.
- Rename `sample.env` to `.env` and fill in with appropriate values.
- **All `*.env` files will be stored to an encrypted TinyDB (`stack.encrypted.json`)**
    - Once the `DB_PASSWORD` is set, do not change the password until the `*.env` files are completely restored.
    - Make sure that the `stack.encrypted.json` doesn't contain values encrypted with multiple passwords.
- Last tested to work with Portainer [2.21.0](https://github.com/portainer/portainer/releases/tag/2.21.0).

## Backup Calendar 📅

> [!NOTE]
> This example comes from our `calendar_md.py` script. Consider running it together with `compose_backup.py` to keep the documentation updated.

<details>
  <summary>October 2023</summary>

   | Mon                       | Tue                       | Wed                       | Thu                       | Fri                       | Sat                       | Sun                       |
   | ------------------------- | ------------------------- | ------------------------- | ------------------------- | ------------------------- | ------------------------- | ------------------------- |
   |                           |                           |                           |                           |                           |                           | [01](/backups/2023/10/01) |
   | [02](/backups/2023/10/02) | [03](/backups/2023/10/03) | [04](/backups/2023/10/04) | [05](/backups/2023/10/05) | [06](/backups/2023/10/06) | [07](/backups/2023/10/07) | [08](/backups/2023/10/08) |
   | [09](/backups/2023/10/09) | [10](/backups/2023/10/10) | [11](/backups/2023/10/11) | [12](/backups/2023/10/12) | [13](/backups/2023/10/13) | [14](/backups/2023/10/14) | [15](/backups/2023/10/15) |
   | [16](/backups/2023/10/16) | [17](/backups/2023/10/17) | [18](/backups/2023/10/18) | [19](/backups/2023/10/19) | [20](/backups/2023/10/20) | [21](/backups/2023/10/21) | [22](/backups/2023/10/22) |
   | [23](/backups/2023/10/23) | [24](/backups/2023/10/24) | [25](/backups/2023/10/25) | [26](/backups/2023/10/26) | [27](/backups/2023/10/27) | [28](/backups/2023/10/28) | [29](/backups/2023/10/29) |
   | [30](/backups/2023/10/30) | [31](/backups/2023/10/31) |                           |                           |                           |                           |                           |
</details>

<details>
  <summary>November 2023</summary>

   | Mon                       | Tue                       | Wed                       | Thu                       | Fri                       | Sat                       | Sun                       |
   | ------------------------- | ------------------------- | ------------------------- | ------------------------- | ------------------------- | ------------------------- | ------------------------- |
   |                           |                           | [01](/backups/2023/11/01) | [02](/backups/2023/11/02) | [03](/backups/2023/11/03) | [04](/backups/2023/11/04) | [05](/backups/2023/11/05) |
   | [06](/backups/2023/11/06) | [07](/backups/2023/11/07) | [08](/backups/2023/11/08) | [09](/backups/2023/11/09) | [10](/backups/2023/11/10) | [11](/backups/2023/11/11) | [12](/backups/2023/11/12) |
   | [13](/backups/2023/11/13) | [14](/backups/2023/11/14) | [15](/backups/2023/11/15) | [16](/backups/2023/11/16) | [17](/backups/2023/11/17) | [18](/backups/2023/11/18) | [19](/backups/2023/11/19) |
   | [20](/backups/2023/11/20) | [21](/backups/2023/11/21) | [22](/backups/2023/11/22) | [23](/backups/2023/11/23) | [24](/backups/2023/11/24) | [25](/backups/2023/11/25) | [26](/backups/2023/11/26) |
   | [27](/backups/2023/11/27) | [28](/backups/2023/11/28) | [29](/backups/2023/11/29) | [30](/backups/2023/11/30) |                           |                           |                           |
</details>

## How to Use? 🚀

1. **Setup and Configuration 🛠️**
   - Clone the repository.
   - Make sure you have `root` access or you are a `sudoers`. We need this to access `/var/lib/docker/volumes/portainer_data/_data`, so, we can export the `docker-compose.yml` files.
   - For the script to commit and push to Git, you need to have configured your Git repo with SSH keys or stored the credentials in the cache.
   - As the user you'll be running the script, run `git config --global --add safe.directory /path/to/compose-backups` to resolve `git` ownership/permission issues.
   - Modify the credentials and paths to your needs.
   - **Git Configurations**

     ```bash
     git config --global user.name "Krishna Alagiri [bot]"
     git config --global user.email "92169357+kalagiri-bot@users.noreply.github.com"
     git config --global --add safe.directory /path/to/compose-backups
     ```

2. **Dependencies 📦**
   - You obviously need `python3` and `git` installed (duh!)
   - The script has several dependencies. To install it, use `sudo pip install -r requirements.txt`.
   - Build the `db-exporter\Dockerfile` to create the `bearlike/portainer-db-exporter:latest` image using:

   ```bash
   cd db-exporter
   docker build -t bearlike/portainer-db-exporter:latest .
   ```

3. **Execution 🚀**
   - Run the script using `python3` in the terminal. For example:

   ```bash
   sudo python3 compose_backup.py
   ```

4. **Logging**
   The script uses basic logging to keep track of its operation. Each logs are stored as `backup.log` in the each backup directories. There is also a `metadata.json` with `docker-compose` stack information(s) exported from portainer.

## Setting Up Daily Cronjob 🕒

1. Open the cron configuration file using your favorite text editor:

   ```bash
   sudo crontab -e
   ```

2. Add a new line at the end of the file using the following format to run the script daily at a specific time (e.g., midnight):

   ```cron
   0 0 * * * /usr/bin/python3 /path/to/compose-backups/compose_backup.py
   ```

3. Save and close the file. The cron daemon will now execute the `compose_backup.py` script every day at the specified time.

## Restore Encrypted `.env` Files 🔄

The `load_env_to_db.py` script provides functionality to backup and restore encrypted `.env` files.

**To restore all `stack.env` files from the backup:**

```bash
python load_env_to_db.py --restore-all --db-password <your_db_password>
```

This command will retrieve all backup entries from the database, decrypt each entry, and write the decrypted content back to its original location.

**To restore a single `stack.env` file from the backup:**

```sh
python load_env_to_db.py --restore <backup_key> --db-password <your_db_password>
```

**Example:**

```sh
python load_env_to_db.py --restore backups/2023/10/16/Hurricane/nextcloud/stack.env --db-password MySecurePassword
```
This command will retrieve the specified backup entry from the database, decrypt it, and write the decrypted content back to its original location.

## Issues? 💬

Having trouble with the script? 💔
Found a bug? 🐞
Do you have an idea for a new featur? 🪄
Let everybody know!

[Create an issue](https://github.com/bearlike/portainer-compose-backup/issues/new)

## Contributions 🎉

Want to help make this project even better? 🤝 Contributions are welcome! ✨
[Fork and submit a pull request](https://github.com/bearlike/portainer-compose-backup/compare/)

## License 📝

This project is released under the MIT License. See [`LICENSE`](LICENSE) for more details.
