# normalize.py

import re
from redis_client import get_redis_client

# Custom Canonical Synonyms (fallback if not in Redis)
custom_synonyms = {
    "not configured":["isn't configured","hasn't been configured", "is unconfigured","missing configuration","was never set up"],
    "TALOS Threat Defense": ["talos", "cisco talos", "talos threat defense"],
    "Spanning Tree Protocol": ["spanning tree", "stp", "802.1d", "spanning tree protocol"],
    "Rapid Spanning Tree Protocol": ["rstp", "802.1w", "rapid spanning tree"],
    "Multiple Spanning Tree Protocol": ["mstp", "802.1s", "multiple spanning tree"],
    "Border Gateway Protocol": ["bgp", "border gateway protocol"],
    "Open Shortest Path First": ["ospf", "open shortest path first"],
    "Network Address Translation": ["nat", "network address translation"],
    "Domain Name System": ["dns", "domain name system"],
    "Dynamic Host Configuration Protocol": ["dhcp", "dynamic host configuration protocol"],
    "Virtual LAN": ["vlan", "virtual lan", "vlan id"],
    "Quality of Service": ["qos", "quality of service"],
    "Access Control List": ["acl", "access control list"],
    "Cisco Umbrella": ["umbrella", "cisco umbrella", "cloud delivered security"],
    "Cisco SecureX": ["securex", "cisco securex"],
    "Cisco XDR": ["xdr", "cisco xdr", "extended detection and response"],
    "Cisco DNA Center": ["dna center", "dnac", "cisco dna center"],
    "Cisco Identity Services Engine": ["ise", "cisco ise", "identity services engine"],
    "Cisco Secure Group Tags": ["sgt", "secure group tag", "secure group tags", "cisco sgt"],
    "Cisco Meraki MX": ["meraki mx", "mx appliance", "meraki security appliance"],
    "Cisco Meraki MR": ["meraki mr", "meraki access point", "mr access point"],
    "Cisco Meraki MS": ["meraki ms", "meraki switch", "ms switch"],
    "Cisco Meraki Systems Manager": ["meraki sm", "systems manager", "meraki mdm"],
    "Cisco Meraki MV Cameras": ["meraki mv", "meraki camera", "mv camera", "meraki mv camera"],
    "Cisco Meraki MT Sensors": ["meraki mt", "meraki sensors", "mt sensor", "power monitor", "environment sensor"],
    "Meraki Auto VPN": ["auto vpn", "meraki auto vpn", "meraki vpn"],
    "Meraki Traffic Shaping": ["traffic shaping", "meraki traffic shaping", "traffic control"],
    "Meraki Content Filtering": ["content filtering", "meraki content filtering"],
    "802.11 WiFi": ["802.11", "wifi", "wireless lan", "wi-fi"],
    "Service Set Identifier (SSID)": ["ssid", "wireless network name", "wifi ssid"],
    "Pre-Shared Key (PSK)": ["psk", "pre-shared key", "wifi password", "wireless password", "wifi psk"],
    "802.1X Authentication": ["802.1x", "dot1x", "wireless 802.1x", "wired 802.1x"],
    "High Availability": ["ha", "high availability", "failover"],
    "Bandwidth Throttle": ["throttle", "throttled"],
    "Megabits Per Second": ["mbps", "megs", "meg", "megabits", "mbits"],
    "Gigabits Per Second": ["gbps", "gigs", "gig", "gigabits", "gbits"],
    "Incorrect":["bad","error","wrong","problem with"],
    "not enabled":["disabled","isn't enabled","isnt enabled"]
}

def populate_cache():
    r = get_redis_client()  # ✅ moved inside function
    for canonical, synonyms in custom_synonyms.items():
        for synonym in synonyms:
            r.hset("acronym_cache", synonym.lower(), canonical)

def normalize_sentence(sentence):
    """
    Normalize a sentence by replacing known technical synonyms with canonical terms.
    Uses Redis as a cache for fast lookups.
    """
    r = get_redis_client()  # ✅ moved inside function
    output = sentence

    # Fetch all keys in the Redis hash
    all_synonyms = r.hkeys("acronym_cache")
    all_synonyms.sort(key=lambda s: -len(s))  # longest match first

    for synonym in all_synonyms:
        pattern = r'\b' + re.escape(synonym) + r'\b'
        match = re.search(pattern, output, flags=re.IGNORECASE)
        if match:
            canonical = r.hget("acronym_cache", synonym)
            if canonical:
                print(f"✅ [CACHE HIT] '{synonym}' → '{canonical}'")
            output = re.sub(pattern, canonical, output, flags=re.IGNORECASE)

    return output

if __name__ == "__main__":
    populate_cache()
    print("✅ Redis acronym_cache populated.")

    print("\n🔧 Technical Term Normalizer")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("Enter a troubleshooting sentence: ").strip()
        if user_input.lower() == "exit":
            break

        result = normalize_sentence(user_input)
        print("\n✅ Normalized:")
        print(result)
        print("\n" + "=" * 60 + "\n")

