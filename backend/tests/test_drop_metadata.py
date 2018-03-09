import base64
from unittest import mock

from syncr_backend.crypto_util import load_public_key
from syncr_backend.drop_metadata import DropMetadata


@mock.patch('syncr_backend.drop_metadata.get_pub_key', autospec=True)
def test_drop_metadata_decode(mock_get_pub_key):

    i = b"ZDc6ZHJvcF9pZDY0OjpzuM/m8jKyJsEhD5WbMz5HdTRprLdR6ETDH3yoiCRgoa5Jk7"\
        b"jvl8sw2iVEwmK6lhZtg99iV7Z1aEIZPNlG7xA1OmZpbGVzZDM6b25lMzI647DEQpj8"\
        b"HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU1OnRocmVlMzI6ptcqx2kPU75q5GuohQ"\
        b"a9lzAqCT9xCEcr2e/Dzv2gZIQzOnR3bzMyOq7AcGRf5T7js3YwWTdhNPBYzDNyR8l4"\
        b"rdF4tszfsAGfZTEwOmZpbGVzX2hhc2gzMjpzniWojj8u7FtbzvHD8pKKSBuyZPQtmQ"\
        b"eNM8ScaVEEHzE2OmhlYWRlcl9zaWduYXR1cmU1MDY6fX2xmb7N078SJn7OF4b105go"\
        b"UN0XA4a46XbwY7NmLFg4spXhazPkRXAA9yNN9B4FUHEF1iGsb2c+jThN1NFCf4F5U2"\
        b"wdPMtOM+75L7KzTHSrWqW8u0M5zTqNwYl0+4GsnwSrZ63O7a1ohqDk+wJ7m9ZTjczU"\
        b"FEi8RJissVaL391phYJocEzKk4hvkrOx3XzNalEImDPAUU/jYKnd2nS0VcIlxk3OOx"\
        b"fjBV2w9EUVzWF9D8jp7R1oVLR+bQ5kHRHWHcnvOAKDJiz8kU0GwtQKEzK1iZFSawso"\
        b"aWcW1+QIzSdvsCUMMuhyRpFXJRGo6Ik/GFxhZcepa4KqhRrTenuhDiEenS5penqBLW"\
        b"toO94Yj/OIzuwXoJdkYGpS5DSekhOwR0iYtCMi0R4NqFM3d4LWjSuIN5d+QPG7aGPo"\
        b"OUI5d117rvWH+AyVAq1lqZrUNKMCuMV0WhHa68cAj/HT1Jlke3SKtYPB0YHxn6gjfc"\
        b"D1ypAcEsEirBMPvdZjCNnojByk89nhKY7++txh/5pz1Nmmf7NvWYteeYgG2lT4FVs/"\
        b"rVLVvKd8KPQR0IpxNWN2d8sWVWrLW8fCY4tVM1V64ZfrQHsHjt0fsfLa9RYUGmj0zp"\
        b"fUVwg0laGaJB6J1zRnpfYmtqWVDWyaO/kVTP6z6pxd66sX6gjyY+1ObcE0Om5hbWU0"\
        b"OnRlc3QxMjpvdGhlcl9vd25lcnNkZTE3OnByZXZpb3VzX3ZlcnNpb25zbGUxMzpwcm"\
        b"ltYXJ5X293bmVyMzI6OnO4z+byMrImwSEPlZszPkd1NGmst1HoRMMffKiIJGAxNjpw"\
        b"cm90b2NvbF92ZXJzaW9uaTFlOTpzaWduZWRfYnkzMjo6c7jP5vIysibBIQ+VmzM+R3"\
        b"U0aay3UehEwx98qIgkYDc6dmVyc2lvbmkxZTEzOnZlcnNpb25fbm9uY2VpMTA2MzQ0"\
        b"OTU2OTA1MTAwNTkwODBlZQ=="

    p = b"LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQ0hEQU5CZ2txaGtpRzl3MEJBUU"\
        b"VGQUFPQ0Fna0FNSUlDQkFLQ0Fmc0EwaE5hdXZ3YjZCRzVlS3oxZ3ltUgpNYlRuekJs"\
        b"SE9iMXFJaXMvV2tXcTFMWWFmaUdaT2YwNVJUTDh0UEQ3NUpvYktGQUtHYVFLWFFQdU"\
        b"lWYk5GeTJJCmFIY3oyRDVMNDNHbW5YN3hoRGJma2NRRGNiSTRCeWpEODg2eVkzTzBC"\
        b"NzNqcWpydUxIL0ZGL0k2eWZxK1RhL3QKUWJJMm5xK05JbWs3cGdwaHNTSnM2TzRiYk"\
        b"5tUytZNFZENDJjN2tEMVArT3RUdk83ZjlwWjlwdGIzOHVNd2gzRApJR05ybXVwSVF1"\
        b"cGI5UDg2WGQ4bWFsVXN5dE5Bd1JEUzJSeTJsU2hEYzc0dVpWYmQ5SzlSSkVmZlpwdl"\
        b"NPdTJrCllJem5vSEk2Z2tyRFNDQkpiNVMyNWs4eXk5Nm1XSjRoLzdiTHh3VnRwWnU0"\
        b"NVZoWDlYT2U1UHMzSGtFNVBHcy8KeDlDeW9mdGoyN3VpbjFJLzZ2UlkvamhFTzNWYm"\
        b"pDTklEdXdyT2FHQ3Rxbk9yd1UzYXhPTnJuR3oySlFRWG16SApFSmlRTXJHVEdJTEs1"\
        b"SGVsU2RWYXVPQlkwWWk4bGIyNTJyblpQeWFaTXRSdkk2MnMrSE9scEpsNGI3SVltck"\
        b"k4CmgxcjNJMGV4ekpCYTNOZnpiS1ZSWFB0MlY5UytTQUVVd20xZWpvMS91cnhWc3lo"\
        b"aFIvQTk0QjQ1K1gzZGdHclMKU1NsSkYrSnV0V2krSGZEL0l0N0ZuOFZhTnVIa0J2b3"\
        b"ZSS1N6OFJodXpmc2pScW5Bc3ZJcEhtRk9CaTRMWDE3RwpNY1lWV0ovQmY2cTQ3Z2dS"\
        b"ZzV4U0FnRngrVG5oZHROdUhpTENZSmx1dGZ0dGpTV0plZmMvV0VYSGtvMkZsbTZ4Cn"\
        b"hwSU40NDJlSDVjRnVxVUNBd0VBQVE9PQotLS0tLUVORCBQVUJMSUMgS0VZLS0tLS0K"

    mock_get_pub_key.return_value = load_public_key(base64.b64decode(p))

    d = DropMetadata.decode(base64.b64decode(i))
    expected_id = b"OnO4z+byMrImwSEPlZszPkd1NGmst1HoRMMffKiIJGChrkmTuO+XyzD"\
                  b"aJUTCYrqWFm2D32JXtnVoQhk82UbvEA=="
    assert base64.b64encode(d.id) == expected_id
