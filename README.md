# lighthaus

## Setting Up

```
# Use pipenv to manage dependencies
pipenv install

pipenv shell # Activate virtual environment
```

## Deploy to Raspberry Pi

```
# Add the git remote
git remote add rasp ssh://pi@192.168.1.45/home/pi/auto-deploy.git

# Deploy to the raspberry pi server
./deploy_rasp.sh
```

### How This Works

There are two servers on the Raspberry Pi involved:

- `auto-deploy.git` - bare git repo that has a post-receive hook
- `lighthaus-autodeploy` - files are copied into here by the post-receive hook


`auto-deploy.git/hooks/post-receive` file

```
#!/bin/sh
git --work-tree=/home/pi/lighthaus-autodeploy --git-dir=/home/pi/auto-deploy.git checkout -f
sudo systemctl stop led
sudo systemctl restart lighthaus-auto
```

The `lighthaus-auto` service runs the `lighthaus.py` file in the `lighthaus-autodeploy/` repository.
