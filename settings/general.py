from os.path import dirname, abspath

run_path = dirname(dirname(abspath(__file__)))

sessions_loc = {
    "ppw": {"location": run_path+"/sessions/ppw", "fernet": True},
    "app_key": {"location": run_path+"/sessions/app_key", "fernet": False}
}