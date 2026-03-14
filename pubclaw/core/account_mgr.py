import json
import os

class AccountManager:
    def __init__(self):
        self.data_dir = os.path.expanduser('~/.pubclaw')
        self.accounts_file = os.path.join(self.data_dir, 'accounts.json')
        os.makedirs(self.data_dir, exist_ok=True)
        self.accounts = self._load()
    
    def _load(self):
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        with open(self.accounts_file, 'w') as f:
            json.dump(self.accounts, f, indent=2)
        os.chmod(self.accounts_file, 0o600)
    
    def add_account(self, platform, account_id, credentials, **kwargs):
        if platform not in self.accounts:
            self.accounts[platform] = []
        
        account = {
            'account_id': account_id,
            'platform': platform,
            'credentials': credentials,
            'status': 'active'
        }
        
        existing = [a for a in self.accounts[platform] if a['account_id'] == account_id]
        if existing:
            idx = self.accounts[platform].index(existing[0])
            self.accounts[platform][idx] = account
        else:
            self.accounts[platform].append(account)
        
        self._save()
        return True
    
    def get_active_account(self, platform):
        if platform not in self.accounts:
            return None
        for acc in self.accounts[platform]:
            if acc['status'] == 'active':
                return acc
        return None
    
    def list_accounts(self):
        result = []
        for plat, accounts in self.accounts.items():
            for acc in accounts:
                result.append({
                    'platform': plat,
                    'account_id': acc['account_id'],
                    'status': acc['status']
                })
        return result
