from pysnmp.hlapi.v3arch.asyncio import get_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
import asyncio

# Standard OID for "Total Marker Count" (Pages Printed)
OID_TOTAL_PAGES = '1.3.6.1.2.1.43.10.2.1.4.1.1'

async def fetch_printer_counter(ip_address: str):
    """
    Talks to the printer over LAN and gets the total page count.
    """
    try:
        iterator = get_cmd(
            SnmpEngine(),
            CommunityData('public', mpModel=0), # 'public' is default password for printers
            UdpTransportTarget().create((ip_address, 161), retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(OID_TOTAL_PAGES))
        ) 

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

        if errorIndication:
            print(f"SNMP Error: {errorIndication}")
            return None
        elif errorStatus:
            print(f"SNMP Error Status: {errorStatus.prettyPrint()}")
            return None
        else:
            # Success! Return the integer value
            counter_value = int(varBinds[0][1])
            return counter_value

    except Exception as e:
        print(f"Connection Error to {ip_address}: {e}")
        return None