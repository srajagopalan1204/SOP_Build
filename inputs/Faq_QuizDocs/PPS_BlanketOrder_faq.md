# PPS – Blanket Order Creation & Processing – PPS Sales  
## Process FAQ

**SOP:** M1. Blanket Order Creation and Processing SOP – PPS Sales  

---

### 1. What is the purpose of the PPS Blanket Order SOP?

The PPS Blanket Order SOP defines the **end-to-end process** for handling blanket orders for generator projects in PPS Sales. It covers:

- The contractor’s initial request for a generator (often with a transfer switch and start-up).  
- How the blanket order is created in the system.  
- How non-stock / modified-build generators are handled.  
- How serialization is set up.  
- How multiple releases (for example, 01 and 02 suffixes) are created and processed.  
- How shipping feedback and AR are completed.  
- How the process hands off to the **Start-Up SOP** once the generator is ready to be started up.

---

### 2. Where does this SOP start and end?

- The process starts at **S1. Contractor Places an Order for a Generator**, including the decision about whether the generator and transfer switch will be shipped together or separately.  
- It ends when the necessary releases have been shipped and invoiced, and the process hands off to **S17. Start-Up SOP** after the customer calls for start-up (S16).  

Between those points, the SOP ensures that the order structure, releases, shipping, and AR are all handled consistently.

---

### 3. Why is the decision about separate shipment (D1) important?

The decision **“Do they want the generator and transfer switch shipped separate?” (D1)** drives how the order and releases are structured:

- If separate shipments are required, additional releases may be created (for example, **3 releases** via S7) so that the generator, transfer switch, and other elements can move on different suffixes.  
- If combined shipment is acceptable, fewer releases may be used (for example, **2 releases** via S18).  

Getting this decision right up front avoids confusion later when pick tickets and invoices are generated.

---

### 4. How are modified-build generators handled (D3, S3, S4)?

When the answer to **D3 – Is the generator a modified build ordered from vendor?** is **Yes**:

- **S3. Create Order as Needed Non-Stock** is used to create an appropriate non-stock order so that the generator can be sourced from the vendor with the correct configuration.  
- **S4. Make a Product Serialized** ensures that the generator is tracked as a **serialized** item, supporting future service, warranty, and start-up tracking.  

If the generator is not a modified build, the process may follow the standard stock or non-stock pattern already defined for that item.

---

### 5. What do S5 (Add Items) and S6 (Add Lump Sum) do on the blanket order?

On the blanket order:

- **S5. Add Items (Including Start-Up)** is used to add item lines such as the generator, transfer switch, start-up, or other related SKUs.  
- **S6. Add Lump Sum** is used to add any **lump-sum** lines that represent agreed package pricing or extra charges that are not tied to a single SKU.  

Together, these steps ensure that the financial value of the blanket order matches what was agreed with the contractor.

---

### 6. How do S7 and S18 (Create Releases) fit into the process?

The steps **S7. Create 3 Releases** and **S18. Create 2 Releases** define how the blanket order will be broken into releases:

- **S7. Create 3 Releases** can be used when the customer and PPS want more granular separation—for example, separate flows for transfer switch, generator, and start-up related work.  
- **S18. Create 2 Releases** can be used when fewer releases are sufficient—for example, one for initial material and one for the generator.  

These releases drive the suffixes (such as **01** and **02**) that show up on pick tickets, shipping feedback, and AR.

---

### 7. What is the role of S8 – Run OEEPC?

**S8. Run OEEPC** is used to process the blanket order through the system’s order engine before the first release moves forward. Depending on your local configuration, this step can:

- Validate pricing and configuration.  
- Generate or update order lines and release structures.  
- Ensure that subsequent steps like pick ticket printing and shipping feedback will run cleanly.  

Running OEEPC at the right time avoids rework later in the release flow.

---

### 8. How does the first release (01 suffix) flow work?

The first release typically uses the **01 suffix** and follows this pattern:

- **S9. Customer Calls For First Release** – the customer indicates they are ready for the first portion (for example, transfer switch or initial material).  
- **S8. Run OEEPC** (if not already run for this release) – to ensure the release is ready.  
- **S10. Print Pick Ticket on 01 Suffix** – the warehouse picks and stages material.  
- **S11. Shipping Feedback** – actual shipped quantities and details are recorded.  
- **S12. “01 Suffix” Goes Through AR Process** – the release is invoiced to the customer.  

This creates a clean financial and physical record for the first release.

---

### 9. What happens in the second release and how does it link to Start-Up?

After the first release is complete, the process continues:

- **S13. Customer Calls For Second Release (Generator)** – the customer is now ready for delivery of the generator.  
- The system checks if the expected number of releases were created (for example, the **D2 – Were 3 Releases Created?** decision).  
- **S14. Print Pick Ticket on 02 Suffix** – the generator is picked.  
- **S15. Shipping Feedback** – the generator shipment is recorded.  
- **S16. Customer Calls For Start-Up** – once the generator is in place, the customer requests start-up.  
- **S17. Start-Up SOP** – control passes to the Start-Up SOP for the field start-up portion.  

This ensures a smooth handoff from sales / blanket order to PPS Service / Start-Up.

---

### 10. How does this Blanket Order SOP tie into the overall PPS / Scott Electric process?

The Blanket Order SOP is one piece of the overall generator project lifecycle:

- **Upstream:** The contractor works with PPS Sales to design and price a solution (generator, transfer switch, start-up).  
- **This SOP:** The Blanket Order is created, configured, and processed through multiple releases, shipping, and AR.  
- **Downstream:** Once the generator has shipped and the customer is ready, the Start-Up SOP is launched (S17), and later PMA or other service offerings may be pursued.  

A disciplined blanket-order process reduces confusion around shipments, invoices, and start-up timing, and sets up PPS and the customer for a well-managed generator project.
