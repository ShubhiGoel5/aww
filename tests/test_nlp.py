import pytest
from src.api.main import extract_search_query, expand_synonyms, detect_domain

def test_extract_search_query_normal():
    assert extract_search_query('what is the punishment for murder?') == 'the punishment for murder'

def test_extract_search_query_multiple_words():
    assert extract_search_query('how long can i be in jail under which law.') == 'be in jail law'

def test_extract_search_query_empty():
    assert extract_search_query('') == ''
    assert extract_search_query('   ') == ''

def test_extract_search_query_none():
    assert extract_search_query(None) == ''

def test_extract_search_query_non_string():
    assert extract_search_query(123) == ''

def test_extract_search_query_unicode():
    assert extract_search_query('what is 😊?') == '😊'

def test_expand_synonyms_mixed_case():
    assert 'indian penal code' in expand_synonyms('IPC section 302')

def test_expand_synonyms_missing():
    assert expand_synonyms('no acronyms here') == []

def test_expand_synonyms_multiple():
    res = expand_synonyms('FIR under IPC')
    assert 'indian penal code' in res
    assert 'first information report' in res

def test_expand_synonyms_empty():
    assert expand_synonyms('') == []
    assert expand_synonyms(None) == []

def test_detect_domain_unambiguous():
    assert detect_domain('what is the punishment for murder') == ['criminal']

def test_detect_domain_ambiguous():
    res = detect_domain('murder contract')
    assert 'criminal' in res
    assert 'civil' in res

def test_detect_domain_empty():
    assert detect_domain('') is None
    assert detect_domain(None) is None
