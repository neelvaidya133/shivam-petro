from bs4 import BeautifulSoup
import pandas as pd

# 1) Paste your full <tbody>…</tbody> HTML below:
html = """
<tbody>
  <tr style="height: 30px">
    <th id="344442271R0" style="height: 30px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 30px">1</div>
    </th>
    <td class="s0">Date</td>
    <td class="s0">Rcpt. No.</td>
    <td class="s0">Slip/Chq./Bill No.</td>
    <td class="s0">Vch. Type</td>
    <td class="s0">Description</td>
    <td class="s0">Debit</td>
    <td class="s0">Credit</td>
    <td class="s0">Balance</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R1" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">2</div>
    </th>
    <td class="s1">01/04/2024</td>
    <td class="s2" colspan="4">Opening Balance</td>
    <td class="s3"></td>
    <td class="s4"></td>
    <td class="s5">11.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R2" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">3</div>
    </th>
    <td class="s6">15/04/2024</td>
    <td class="s7"></td>
    <td class="s8">27</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">12,546.00</td>
    <td class="s11"></td>
    <td class="s12">12,557.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R3" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">4</div>
    </th>
    <td class="s6">30/04/2024</td>
    <td class="s7"></td>
    <td class="s8">139</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">9,127.00</td>
    <td class="s11"></td>
    <td class="s12">21,684.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R4" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">5</div>
    </th>
    <td class="s6">06/05/2024</td>
    <td class="s8">159</td>
    <td class="s8">159</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">21,673.00</td>
    <td class="s12">11.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R5" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">6</div>
    </th>
    <td class="s6">15/05/2024</td>
    <td class="s7"></td>
    <td class="s8">244</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">9,979.00</td>
    <td class="s11"></td>
    <td class="s12">9,990.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R6" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">7</div>
    </th>
    <td class="s6">31/05/2024</td>
    <td class="s7"></td>
    <td class="s8">349</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">5,313.00</td>
    <td class="s11"></td>
    <td class="s12">15,303.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R7" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">8</div>
    </th>
    <td class="s6">11/06/2024</td>
    <td class="s8">350</td>
    <td class="s8">349</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">15,293.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R8" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">9</div>
    </th>
    <td class="s6">15/06/2024</td>
    <td class="s7"></td>
    <td class="s8">464</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">10,977.00</td>
    <td class="s11"></td>
    <td class="s12">10,987.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R9" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">10</div>
    </th>
    <td class="s6">30/06/2024</td>
    <td class="s7"></td>
    <td class="s8">564</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">4,735.00</td>
    <td class="s11"></td>
    <td class="s12">15,722.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R10" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">11</div>
    </th>
    <td class="s6">05/07/2024</td>
    <td class="s8">478</td>
    <td class="s8">478</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">15,712.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R11" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">12</div>
    </th>
    <td class="s6">15/07/2024</td>
    <td class="s7"></td>
    <td class="s8">663</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">10,665.00</td>
    <td class="s11"></td>
    <td class="s12">10,675.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R12" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">13</div>
    </th>
    <td class="s6">31/07/2024</td>
    <td class="s7"></td>
    <td class="s8">733</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">8,346.00</td>
    <td class="s11"></td>
    <td class="s12">19,021.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R13" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">14</div>
    </th>
    <td class="s6">15/08/2024</td>
    <td class="s7"></td>
    <td class="s8">815</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">11,442.00</td>
    <td class="s11"></td>
    <td class="s12">30,463.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R14" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">15</div>
    </th>
    <td class="s6">31/08/2024</td>
    <td class="s7"></td>
    <td class="s8">896</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">5,691.00</td>
    <td class="s11"></td>
    <td class="s12">36,154.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R15" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">16</div>
    </th>
    <td class="s6">06/09/2024</td>
    <td class="s8">742</td>
    <td class="s8">742</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TYRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">17,133.00</td>
    <td class="s12">19,021.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R16" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">17</div>
    </th>
    <td class="s6">06/09/2024</td>
    <td class="s8">743</td>
    <td class="s8">743</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">19,011.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R17" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">18</div>
    </th>
    <td class="s6">15/09/2024</td>
    <td class="s7"></td>
    <td class="s8">978</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">5,939.00</td>
    <td class="s11"></td>
    <td class="s12">5,949.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R18" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">19</div>
    </th>
    <td class="s6">30/09/2024</td>
    <td class="s7"></td>
    <td class="s8">1056</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">10,969.00</td>
    <td class="s11"></td>
    <td class="s12">16,918.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R19" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">20</div>
    </th>
    <td class="s6">09/10/2024</td>
    <td class="s8">899</td>
    <td class="s8">898</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">16,908.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R20" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">21</div>
    </th>
    <td class="s6">15/10/2024</td>
    <td class="s7"></td>
    <td class="s8">1150</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">2,688.00</td>
    <td class="s11"></td>
    <td class="s12">2,698.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R21" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">22</div>
    </th>
    <td class="s6">31/10/2024</td>
    <td class="s7"></td>
    <td class="s8">1236</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">2,351.00</td>
    <td class="s11"></td>
    <td class="s12">5,049.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R22" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">23</div>
    </th>
    <td class="s6">13/11/2024</td>
    <td class="s8">1056</td>
    <td class="s8">1054</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">5,039.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R23" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">24</div>
    </th>
    <td class="s6">15/11/2024</td>
    <td class="s7"></td>
    <td class="s8">1327</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">5,839.00</td>
    <td class="s11"></td>
    <td class="s12">5,849.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R24" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">25</div>
    </th>
    <td class="s6">30/11/2024</td>
    <td class="s7"></td>
    <td class="s8">1421</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">9,930.00</td>
    <td class="s11"></td>
    <td class="s12">15,779.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R25" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">26</div>
    </th>
    <td class="s6">05/12/2024</td>
    <td class="s8">1158</td>
    <td class="s8">1155</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">15,769.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R26" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">27</div>
    </th>
    <td class="s6">15/12/2024</td>
    <td class="s7"></td>
    <td class="s8">1532</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">12,558.00</td>
    <td class="s11"></td>
    <td class="s12">12,568.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R27" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">28</div>
    </th>
    <td class="s6">31/12/2024</td>
    <td class="s7"></td>
    <td class="s8">1636</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">6,841.00</td>
    <td class="s11"></td>
    <td class="s12">19,409.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R28" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">29</div>
    </th>
    <td class="s6">09/01/2025</td>
    <td class="s8">1359</td>
    <td class="s8">1355</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">19,399.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R29" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">30</div>
    </th>
    <td class="s6">15/01/2025</td>
    <td class="s7"></td>
    <td class="s8">1737</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">7,029.00</td>
    <td class="s11"></td>
    <td class="s12">7,039.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R30" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">31</div>
    </th>
    <td class="s6">31/01/2025</td>
    <td class="s7"></td>
    <td class="s8">1838</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">8,586.00</td>
    <td class="s11"></td>
    <td class="s12">15,625.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R31" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">32</div>
    </th>
    <td class="s6">05/02/2025</td>
    <td class="s8">1507</td>
    <td class="s8">1503</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">15,615.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R32" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">33</div>
    </th>
    <td class="s6">15/02/2025</td>
    <td class="s7"></td>
    <td class="s8">1943</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">11,810.00</td>
    <td class="s11"></td>
    <td class="s12">11,820.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R33" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">34</div>
    </th>
    <td class="s6">28/02/2025</td>
    <td class="s7"></td>
    <td class="s8">2044</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">9,036.00</td>
    <td class="s11"></td>
    <td class="s12">20,856.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R34" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">35</div>
    </th>
    <td class="s6">06/03/2025</td>
    <td class="s8">1676</td>
    <td class="s8">1671</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">20,846.00</td>
    <td class="s12">10.00 Dr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R35" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">36</div>
    </th>
    <td class="s6">15/03/2025</td>
    <td class="s7"></td>
    <td class="s8">2142</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">6,981.00</td>
    <td class="s11"></td>
    <td class="s12">6,991.00 Dr</td>
  </tr>
  <tr style="height: 28px">
    <th id="344442271R36" style="height: 28px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 28px">37</div>
    </th>
    <td class="s6">29/03/2025</td>
    <td class="s8">1806</td>
    <td class="s8">1801</td>
    <td class="s6">BB</td>
    <td class="s9">State Bank Of India - 5182<br />Narr.: TRF Inst.: Sbi.</td>
    <td class="s10"></td>
    <td class="s11">13,633.00</td>
    <td class="s12">6,642.00 Cr</td>
  </tr>
  <tr style="height: 17px">
    <th id="344442271R37" style="height: 17px" class="row-headers-background">
      <div class="row-header-wrapper" style="line-height: 17px">38</div>
    </th>
    <td class="s6">31/03/2025</td>
    <td class="s7"></td>
    <td class="s8">2243</td>
    <td class="s6">SB</td>
    <td class="s9">SALES ACCOUNT</td>
    <td class="s10">6,652.00</td>
    <td class="s11"></td>
    <td class="s12">10.00 Dr</td>
  </tr>
</tbody
"""

# 2) Parse it
soup = BeautifulSoup(html, "html.parser")
rows = soup.find_all("tr")

# 3) Build a list of rows
data = []
for row in rows:
    # Skip the row-number TH, keep the next 8 cells (Date → Balance)
    cells = row.find_all(["td", "th"])[1:9]
    texts = []
    for cell in cells:
        text = cell.get_text(separator=" ", strip=True)
        texts.append(text if text else "0")
    data.append(texts)

# 4) First row becomes header
headers = data[0]
df = pd.DataFrame(data[1:], columns=headers)

# 5) Ensure no NaNs remain
df = df.fillna("0")

# 6) Save to CSV
csv_path = r"C:\Users\neelv\Documents\ledger.csv"
df.to_csv(csv_path, index=False)
print(f"CSV written to: {csv_path}\n")

# 7) Show first and last rows
print("First row:")
print(df.iloc[0].to_dict(), "\n")
print("Last row:")
print(df.iloc[-1].to_dict())
