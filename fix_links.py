import os

def replace_in_dir(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "back to MAL site" in content:
                    new_content = content.replace("back to MAL site", "back to SbL site")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1
    print(f"Replaced text in {count} files in {directory}.")

if __name__ == "__main__":
    replace_in_dir("html_analyses/examples")
    replace_in_dir("html_sbl_analyses/examples")
