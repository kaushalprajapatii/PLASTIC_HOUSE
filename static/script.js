/* =====================================================
   ADD TO CART FUNCTION
===================================================== */

async function addCart(btn){

    let item = btn.dataset.name
    let price = btn.dataset.price
    let image = btn.dataset.image
    let qtyId = btn.dataset.id

    let qtyInput = document.getElementById(qtyId)
    let qty = parseInt(qtyInput.value)

   let maxStock = parseInt(btn.dataset.stock)


    if(qty <= 0){
        showPopup("Please select quantity first","error")
        return
    }

    if(qty > maxStock){
        showPopup("Quantity exceeds available stock","error")
        return
    }

    btn.disabled = true
    btn.innerText = "Adding..."

    let form = new FormData()
    form.append("item", item)
    form.append("qty", qty)
    form.append("price", price)
    form.append("image", image)

    try{

        let res = await fetch("/add_to_cart", {
            method:"POST",
            body:form
        })

        let data = await res.json()

        showPopup(data.message,"success")
        qtyInput.value = 0

    }catch{
        showPopup("Error adding item","error")
    }

    btn.disabled = false
    btn.innerText = "Add To Cart"
}


/* =====================================================
   POPUP NOTIFICATION
===================================================== */

function showPopup(message, type){

    let popup = document.getElementById("popup")
    if(!popup) return

    popup.innerText = message

    popup.classList.remove("popup-success","popup-error")

    if(type === "success"){
        popup.classList.add("popup-success")
    }else{
        popup.classList.add("popup-error")
    }

    popup.style.display = "block"

    setTimeout(()=>{
        popup.style.display = "none"
    },2000)
}


/* =====================================================
   QUANTITY VALIDATION
===================================================== */

document.addEventListener("input", function(e){

    if(e.target.type === "number"){
        if(e.target.value < 0){
            e.target.value = 0
        }
    }

})


/* =====================================================
   PAYMENT METHOD HANDLING
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    let radios = document.querySelectorAll("input[name='pay']")
    let upiSection = document.getElementById("upiBox")

    radios.forEach(radio => {

        radio.addEventListener("change", () => {

            if(!upiSection) return

            if(radio.value === "upi" && radio.checked){
                upiSection.style.display = "block"
            }else{
                upiSection.style.display = "none"
            }

        })

    })

})


/* =====================================================
   BUTTON CLICK ANIMATION
===================================================== */

document.addEventListener("click", function(e){

    if(e.target.tagName === "BUTTON"){

        e.target.classList.add("btn-click")

        setTimeout(()=>{
            e.target.classList.remove("btn-click")
        },150)

    }

})


/* =====================================================
   MEDIA PREVIEW MODAL (UPDATED)
   - Supports multiple images & videos
   - Supports old single image preview
===================================================== */

function openPreview(element){

    let modal = document.getElementById("mediaModal") || document.getElementById("imgModal")
    let container = document.getElementById("mediaContainer")
    let modalImg = document.getElementById("modalImg")

    if(!modal) return

    /* ---------- NEW MULTI MEDIA PREVIEW ---------- */
    let mediaData = element.getAttribute("data-media")

    if(mediaData && container){

        let mediaList = []

        try{
            mediaList = JSON.parse(mediaData)
        }catch{
            mediaList = []
        }

        container.innerHTML = ""

        mediaList.forEach(file => {

            if(file.endsWith(".mp4")){

                container.innerHTML += `
                <video controls style="max-width:90%">
                    <source src="/static/images/${file}">
                </video>
                `

            }else{

                container.innerHTML += `
                <img src="/static/images/${file}" style="max-width:90%">
                `

            }

        })

        modal.style.display = "flex"
        return
    }

    /* ---------- OLD SINGLE IMAGE PREVIEW ---------- */
    if(modalImg && typeof element === "string"){
        modal.style.display = "flex"
        modalImg.src = element
    }

}


function closePreview(){

    let modal = document.getElementById("mediaModal") || document.getElementById("imgModal")

    if(modal){
        modal.style.display = "none"
    }

}


/* =====================================================
   CLOSE MODAL ON ESC
===================================================== */

document.addEventListener("keydown", function(e){

    if(e.key === "Escape"){
        closePreview()
    }

})


/* =====================================================
   CLOSE MODAL IF CLICK OUTSIDE
===================================================== */

document.addEventListener("click", function(e){

    let modal = document.getElementById("mediaModal") || document.getElementById("imgModal")

    if(e.target === modal){
        closePreview()
    }

})
