import os
os.environ['SHADOWFORGE_MODE'] = 'debug'
os.environ['SHADOWFORGE__NVIDIA__API_KEY'] = 'env-key'
from core.config import ShadowForgeConfig, ModoOperacao, ConfigNVIDIA
print('ENV:', os.environ.get('SHADOWFORGE_MODE'), os.environ.get('SHADOWFORGE__NVIDIA__API_KEY'))
modo_str = os.environ.get('SHADOWFORGE_MODE', 'stealth')
print('modo_str:', repr(modo_str))
modo_enum = ModoOperacao(modo_str)
print('modo_enum:', modo_enum, type(modo_enum))
cfg = ShadowForgeConfig(nvidia=ConfigNVIDIA(), modo=modo_enum)
print('Created manually modo:', cfg.modo)
print('Created manually nvidia.api_key:', cfg.nvidia.api_key)
# Now test the class method
print('Testing carregar_de_env:')
cfg3 = ShadowForgeConfig.carregar_de_env()
print('carregar_de_env modo:', cfg3.modo)
print('carregar_de_env nvidia.api_key:', cfg3.nvidia.api_key)
