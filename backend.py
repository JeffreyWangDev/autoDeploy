import subprocess
import re
import sqlite3
import docker

def create_database_table(db_path="server_deployments.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            subdomain TEXT NOT NULL, 
            main_domain TEXT NOT NULL,
            port INTEGER NOT NULL,
            image_link TEXT,
            extra_flags TEXT,
            on_off INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def get_open_port(is_last=False):
    cmd = [ "nest", "get_port"]
    output = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0]
    regex = re.compile(r"([0-9]*)")
    found = re.findall(regex,str(output))
    found.sort()
    open_port = found[-1]
    if is_last:
        try:
            return int(open_port)
        except:
            return None
    else:
        try:
            return int(open_port)
        except:
            return get_open_port(True)

def register_subdomain(subdomain, main_domain, port):
    """Registers a subdomain using the 'nest caddy add' command."""
    cmd = ["nest", "caddy", "add", f"{subdomain}.{main_domain}", "--proxy", f":{port}"]
    try:
        subprocess.check_call(cmd)  # Check for errors
        print(f"Subdomain '{subdomain}.{main_domain}' registered successfully on port {port}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error registering subdomain: {e}")
        return False

def run_docker_container(image_link, container_name, port, extra_flags=None):
    """Runs a Docker container using the docker-py library."""
    try:
        client = docker.from_env() 

        port_mappings = {80: port} 

        environment = {}
        if extra_flags:
            for i in range(0, len(extra_flags), 2): 
                if extra_flags[i] == "-e":
                    environment[extra_flags[i+1].split("=")[0]] = extra_flags[i+1].split("=")[1]
            cleaned_extra_flags = [flag for flag in extra_flags if flag != "-e"]
        else:
            cleaned_extra_flags = None




        container = client.containers.run(
            image_link,
            name=container_name,
            ports=port_mappings,
            detach=True,
            environment=environment, 
            volumes = cleaned_extra_flags
        )

        print(f"Docker container '{container_name}' started (detached mode - docker-py). Container ID: {container.id}")
        return True



    except docker.errors.APIError as e:
        print(f"Error running Docker container: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
def deploy_new_server(image_link, name, docker_flags=None, db_path="server_deployments.db"): 
    """Deploys a new server and saves data to an SQLite database."""
    main_domain = "jeffrey.hackclub.app"
    create_database_table(db_path)
    
    port = get_open_port()
    if port is None:
        return False

    name = name.lower()

    if run_docker_container(image_link, name, port, docker_flags) and register_subdomain(name, main_domain, port):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            flags_string = ", ".join(docker_flags) if docker_flags else None  

            cursor.execute('''
                INSERT INTO deployments (name, subdomain, main_domain, port, image_link, extra_flags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, name, main_domain, port, image_link, flags_string)) 
            conn.commit()
            conn.close()
            print(f"Deployment data saved to database.")
            
            
        except sqlite3.IntegrityError:
            print(f"Error: A server with the name '{name}' already exists in the database.")
            return False
        except Exception as e:
            print(f"Error saving deployment data to database: {e}")
            return False
            
        print(f"Server deployed successfully: {name}.{main_domain}")
        return True
    else:
        print("Server deployment failed.")
        return False

def remove_server(name, db_path="server_deployments.db"):
    """Removes a server, including its Docker container, Caddy config, and database entry."""
    try:
        client = docker.from_env()
        container = client.containers.get(name) 
        container.stop()
        container.remove()
        print(f"Docker container '{name}' removed.")
      
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT main_domain, port FROM deployments WHERE name=?", (name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            
            main_domain, port = result
            cmd = ["nest", "caddy", "rm", f"{name}.{main_domain}"] # Check caddy remove syntax
            subprocess.check_call(cmd)
            print(f"Caddy configuration for '{name}.{main_domain}' removed.")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deployments WHERE name=?", (name,))
        conn.commit()
        conn.close()
        print(f"Server '{name}' removed from database.")
        return True


    except docker.errors.NotFound:
        print(f"Error: Docker container '{name}' not found.")
        return False
    except Exception as e: 
        print(f"An error occurred: {e}")
        return False


def stop_server(name, db_path="server_deployments.db"):
    """Stops a server's Docker container and updates its status in the database."""
    try:
        client = docker.from_env()
        container = client.containers.get(name)
        container.stop()
        print(f"Docker container '{name}' stopped.")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE deployments SET on_off = 0 WHERE name = ?", (name,)) 
        conn.commit()
        conn.close()
        print(f"Server '{name}' status updated in database (stopped).")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error stopping server: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False    


def start_server(name, db_path="server_deployments.db"):
    try:
        client = docker.from_env()
        container = client.containers.get(name)
        container.start()
        print(f"Docker container '{name}' started.")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE deployments SET on_off = 1 WHERE name = ?", (name,)) 
        conn.commit()
        conn.close()
        print(f"Server '{name}' status updated in database (started).")
        return True

    except docker.errors.NotFound:
        print(f"Error: Docker container '{name}' not found.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False  
    