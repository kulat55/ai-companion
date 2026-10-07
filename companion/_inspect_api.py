# -*- coding: utf-8 -*-
import urllib.request, json
spec = json.load(urllib.request.urlopen("http://127.0.0.1:8283/openapi.json"))
op = spec["paths"]["/v1/providers/"]["post"]
rb = op["requestBody"]["content"]["application/json"]["schema"]
ref = rb.get("$ref", "")
print("request schema ref:", ref)
comps = spec["components"]["schemas"]
name = ref.split("/")[-1]
if name in comps:
    sch = comps[name]
    for k, v in sch.get("properties", {}).items():
        t = v.get("type", v.get("anyOf", v.get("$ref", "")))
        print(" -", k, ":", t)
print("\n--- check endpoint request ---")
op2 = spec["paths"]["/v1/providers/check"]["post"]
rb2 = op2["requestBody"]["content"]["application/json"]["schema"]
print(rb2.get("$ref", rb2))
