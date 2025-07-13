from flask import Blueprint, render_template, request, redirect, url_for, flash
from web.src.models.pet import db, Pet  # 修正済みインポート
from web.src.forms.pet_form import PetForm

pet_bp = Blueprint('pet', __name__)

@pet_bp.route('/')
def list_pets():
    pets = Pet.query.order_by(Pet.created_at.desc()).all()
    print(f"[DEBUG] pets in DB: {pets}")
    for pet in pets:
        print(f"[DEBUG] pet: id={pet.id}, name={pet.name}, species={pet.species}, sex={pet.sex}, created_at={pet.created_at}")
    form = PetForm()
    return render_template('index.html', pets=pets, form=form)

@pet_bp.route('/', methods=['POST'])
def create_pet():
    form = PetForm()
    if form.validate_on_submit():
        pet = Pet(
            name=form.name.data,
            species=form.species.data,
            sex=form.sex.data
        )
        db.session.add(pet)
        db.session.commit()
        flash('ペットを登録しました！', 'success')
        return redirect(url_for('pet.list_pets'))
    return render_template('index.html', form=form)

@pet_bp.route('/pets/<int:id>')
def get_pet(id):
    pet = Pet.query.get_or_404(id)
    return render_template('detail.html', pet=pet)

@pet_bp.route('/pets/<int:id>/edit', methods=['GET', 'POST'])
def edit_pet(id):
    pet = Pet.query.get_or_404(id)
    form = PetForm(obj=pet)
    if request.method == 'POST' and form.validate_on_submit():
        pet.name = form.name.data
        pet.species = form.species.data
        pet.sex = form.sex.data
        db.session.commit()
        flash('ペット情報を更新しました！', 'success')
        return redirect(url_for('pet.get_pet', id=pet.id))
    return render_template('edit.html', form=form, pet=pet)

@pet_bp.route('/pets/<int:id>/delete', methods=['POST'])
def delete_pet(id):
    pet = Pet.query.get_or_404(id)
    db.session.delete(pet)
    db.session.commit()
    flash('ペットを削除しました！', 'success')
    return redirect(url_for('pet.list_pets'))
