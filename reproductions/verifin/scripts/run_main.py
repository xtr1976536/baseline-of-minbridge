"""Load the encrypted, user-authorized gateway credential into this process only."""
import os
from provider_credential import load
if not os.environ.get('VF_AIWANWU_API_KEY'):
    os.environ['VF_AIWANWU_API_KEY']=load()
from vf_repro.runner import main
if __name__=='__main__':main()
