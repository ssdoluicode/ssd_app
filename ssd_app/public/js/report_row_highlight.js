
document.addEventListener("click", function (e) {
    const row = e.target.closest(".datatable .dt-row");
    if (!row) return;

    document
        .querySelectorAll(".datatable .dt-row")
        .forEach(r => r.classList.remove("report-row-selected"));

    row.classList.add("report-row-selected");
});
