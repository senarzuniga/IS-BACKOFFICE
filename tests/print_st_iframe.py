import streamlit as st
import inspect

print('signature:', inspect.signature(st.iframe))
print('\n'.join(st.iframe.__doc__.split('\n')[:10]))
