import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmDeleteRecordingModalComponent } from './confirm-delete-recording-modal.component';

describe('ConfirmDeleteRecordingModalComponent', () => {
  let component: ConfirmDeleteRecordingModalComponent;
  let fixture: ComponentFixture<ConfirmDeleteRecordingModalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ConfirmDeleteRecordingModalComponent]
    });
    fixture = TestBed.createComponent(ConfirmDeleteRecordingModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
