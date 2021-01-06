git pull origin main
cd /home/ubuntu/teg/actions/
sudo mkdir -p releases
sudo ansible-galaxy collection build -v --force --output-path releases/
cd releases
LATEST=$(ls pystol-actions*.tar.gz | grep -v latest | sort -V | tail -n1)
sudo ln -sf $LATEST pystol-actions-latest.tar.gz
ansible-galaxy collection install --force pystol-actions-latest.tar.gz
cd /home/ubuntu/teg/actions/roles/killpods/tasks/

